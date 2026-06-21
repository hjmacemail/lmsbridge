"""Map a validated LTI launch onto local users, courses, and enrollments (JIT provisioning)."""
from __future__ import annotations

import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password
from app.lti import services
from app.lti.claims import is_admin_role, is_instructor
from app.lti.launch import LtiLaunch
from app.models.course import Course, Enrollment
from app.models.enums import UserRole
from app.models.lti import LtiRegistration
from app.models.tenant import Tenant
from app.models.user import User

logger = get_logger("lti.provisioning")


def get_or_create_tenant(db: Session, launch: LtiLaunch) -> Tenant:
    """One tenant (institution) per LTI registration."""
    reg = launch.registration
    tenant = db.scalar(select(Tenant).where(Tenant.lti_registration_id == reg.id))
    if tenant:
        return tenant
    tenant = Tenant(name=reg.name or reg.issuer, slug=f"reg-{reg.id}", lti_registration_id=reg.id)
    db.add(tenant)
    db.flush()
    return tenant


def _stable_user_key(launch: LtiLaunch) -> str:
    # Globally unique across platforms: issuer + platform subject.
    return f"lti::{launch.registration.issuer}::{launch.sub}"


def _course_key(launch: LtiLaunch) -> str:
    return f"lti::{launch.registration.issuer}::{launch.context_id}"


def _role_from_roles(roles: list[str]) -> UserRole:
    # LMS Administrator/sysadmin -> institution admin (scoped to their tenant; never platform).
    if is_admin_role(roles):
        return UserRole.admin
    if is_instructor(roles):
        return UserRole.instructor
    return UserRole.student


def _role_for(launch: LtiLaunch) -> UserRole:
    return _role_from_roles(launch.roles)


def provision(db: Session, launch: LtiLaunch) -> tuple[User, Course | None, str]:
    role = _role_for(launch)
    tenant = get_or_create_tenant(db, launch)

    ext = _stable_user_key(launch)
    user = db.scalar(select(User).where(User.external_id == ext))
    if not user:
        # Email may be absent or shared across platforms; synthesize a unique fallback.
        email = launch.email or f"{secrets.token_hex(8)}@lti.local"
        if db.scalar(select(User).where(User.email == email)):
            email = f"{secrets.token_hex(8)}+{email}"
        user = User(
            email=email,
            full_name=launch.name or "LMS User",
            external_id=ext,
            role=role,
            tenant_id=tenant.id,
            hashed_password=hash_password(secrets.token_urlsafe(24)),
        )
        db.add(user)
        db.flush()
    else:
        # Don't downgrade an existing higher role (student < instructor < admin).
        rank = {UserRole.student: 0, UserRole.instructor: 1, UserRole.admin: 2}
        if rank[role] > rank[user.role]:
            user.role = role
        if launch.name:
            user.full_name = launch.name
        user.tenant_id = tenant.id

    course: Course | None = None
    if launch.context_id:
        ckey = _course_key(launch)
        course = db.scalar(select(Course).where(Course.brightspace_course_id == ckey))
        if not course:
            # The course's stable identity is its LTI key (brightspace_course_id). The
            # (code, term) unique constraint, however, would collide whenever two distinct
            # LTI contexts share a title under term "LTI" (different courses, even different
            # platforms). Disambiguate the human-readable code with a short stable suffix
            # derived from the LTI key so provisioning never violates that constraint.
            suffix = hashlib.sha1(ckey.encode("utf-8")).hexdigest()[:6]
            label = (launch.context_title or launch.context_id or "Course")[:50]
            course = Course(
                code=f"{label} [{suffix}]",
                title=launch.context_title or "LTI Course",
                term="LTI",
                brightspace_course_id=ckey,
                tenant_id=tenant.id,
            )
            db.add(course)
            db.flush()
        elif course.tenant_id is None:
            course.tenant_id = tenant.id
        # Capture the NRPS membership endpoint so the full roster can be (re)synced later.
        nrps_url = (launch.nrps or {}).get("context_memberships_url")
        if nrps_url:
            course.lti_memberships_url = nrps_url
        # Capture the AGS line-items endpoint so assessments can be (re)synced later.
        lineitems_url = (launch.ags or {}).get("lineitems")
        if lineitems_url:
            course.lti_lineitems_url = lineitems_url
        # Ensure enrollment.
        enr = db.scalar(
            select(Enrollment).where(
                Enrollment.user_id == user.id, Enrollment.course_id == course.id
            )
        )
        if not enr:
            db.add(Enrollment(user_id=user.id, course_id=course.id, role=role))

    db.commit()
    db.refresh(user)
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return user, course, token


_ROLE_RANK = {UserRole.student: 0, UserRole.instructor: 1, UserRole.admin: 2}


def sync_course_roster(db: Session, reg: LtiRegistration, course: Course) -> dict:
    """Import the full course roster from the LMS via NRPS into local users + enrollments.

    Uses the membership URL captured at launch (``course.lti_memberships_url``). Returns a
    summary dict. Idempotent: users/enrollments are upserted, never duplicated.
    """
    url = course.lti_memberships_url
    if not url:
        return {"synced": 0, "members": 0, "skipped": "no_membership_url"}

    members = services.nrps_get_members(db, reg, url)
    synced = 0
    for m in members:
        # NRPS may include Inactive/Deleted members — only enroll active ones.
        if (m.get("status") or "Active") != "Active":
            continue
        sub = m.get("user_id")
        if not sub:
            continue
        roles = m.get("roles", []) or []
        role = _role_from_roles(roles)
        ext = f"lti::{reg.issuer}::{sub}"

        user = db.scalar(select(User).where(User.external_id == ext))
        if not user:
            email = m.get("email") or f"{secrets.token_hex(8)}@lti.local"
            if db.scalar(select(User).where(User.email == email)):
                email = f"{secrets.token_hex(8)}+{email}"
            user = User(
                email=email,
                full_name=m.get("name") or "LMS User",
                external_id=ext,
                role=role,
                tenant_id=course.tenant_id,
                hashed_password=hash_password(secrets.token_urlsafe(24)),
            )
            db.add(user)
            db.flush()
        else:
            if _ROLE_RANK[role] > _ROLE_RANK[user.role]:
                user.role = role
            if m.get("name"):
                user.full_name = m["name"]

        enr = db.scalar(
            select(Enrollment).where(
                Enrollment.user_id == user.id, Enrollment.course_id == course.id
            )
        )
        if not enr:
            db.add(Enrollment(user_id=user.id, course_id=course.id, role=role))
        synced += 1

    db.commit()
    logger.info("NRPS roster sync: course=%s synced=%d of %d", course.id, synced, len(members))
    return {"synced": synced, "members": len(members)}


def maybe_sync_roster_on_launch(db: Session, launch: LtiLaunch, course: Course | None) -> None:
    """Best-effort roster import triggered by an instructor/admin launch. Never raises."""
    if course is None:
        return
    if _role_from_roles(launch.roles) not in (UserRole.instructor, UserRole.admin):
        return
    if not (launch.nrps or {}).get("context_memberships_url"):
        return
    try:
        sync_course_roster(db, launch.registration, course)
    except Exception as e:  # noqa: BLE001 — roster sync must never break a launch
        db.rollback()
        logger.warning("NRPS roster sync failed for course=%s: %s", course.id, e)
