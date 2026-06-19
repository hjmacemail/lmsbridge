"""Seed demo data and exercise the full remediation pipeline.

Usage:
    python -m app.scripts.seed              # seed (idempotent-ish)
    python -m app.scripts.seed --if-empty   # only seed when DB has no users
    python -m app.scripts.seed --reset      # drop + recreate all tables, then seed
"""
from __future__ import annotations

import argparse

from sqlalchemy import select

from app.core.logging import configure_logging, get_logger
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.concept import Concept
from app.models.course import Course, Enrollment
from app.models.enums import UserRole
from app.models.user import User
from app.services.sync_service import sync_course_results

logger = get_logger("seed")

CONCEPTS = {
    "BS-CS201": [
        ("binary_representation", "Binary Representation", "How integers map to bits.", 0, []),
        ("binary_arithmetic", "Binary Arithmetic", "Adding/subtracting in base 2.", 1,
         ["binary_representation"]),
        ("boolean_logic", "Boolean Logic", "AND/OR/NOT and truth tables.", 2, []),
        ("machine_code", "Machine-Level Computation", "From instructions to execution.", 3,
         ["binary_arithmetic", "boolean_logic"]),
    ],
    "BS-CS310": [
        ("encapsulation", "Encapsulation", "Bundling state with behavior.", 0, []),
        ("inheritance", "Inheritance", "Deriving classes from base classes.", 1,
         ["encapsulation"]),
        ("polymorphism", "Polymorphism", "One interface, many implementations.", 2,
         ["inheritance"]),
        ("data_structures", "Data Structures", "Lists, trees, hash maps.", 3, []),
    ],
    "BS-DS200": [
        ("probability_basics", "Probability Basics", "Sample spaces and events.", 0, []),
        ("conditional_probability", "Conditional Probability", "P(A|B) and Bayes.", 1,
         ["probability_basics"]),
        ("distributions", "Distributions", "Common discrete/continuous distributions.", 2,
         ["probability_basics"]),
        ("hypothesis_testing", "Hypothesis Testing", "Null/alternative, p-values.", 3,
         ["conditional_probability", "distributions"]),
    ],
}

COURSES = [
    ("CS-UY 2110", "Computer Architecture & Digital Logic", "2026SP", "BS-CS201"),
    ("CS-UY 2124", "Object-Oriented Programming", "2026SP", "BS-CS310"),
    ("DS-UY 2003", "Statistical Reasoning for Data Science", "2026SP", "BS-DS200"),
]


def _get_or_create_user(db, email, name, role, password="changeme123"):
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(email=email, full_name=name, role=role, hashed_password=hash_password(password))
    db.add(user)
    db.flush()
    return user


# Sample lecture-note text per (course, concept_key) used to ground remediation.
_MATERIALS = {
    "BS-CS201": {
        "binary_arithmetic": (
            "Lecture 2 — Binary Arithmetic.\n"
            "To add two binary numbers, add column by column from the least significant bit. "
            "When a column sums to 2 (10 in binary), write 0 and carry 1 to the next column; "
            "when it sums to 3 (11), write 1 and carry 1. The carry rule is the single most "
            "common source of error: always resolve the carry before moving left. Subtraction "
            "uses two's complement: invert the bits of the subtrahend and add 1, then add."
        ),
    },
    "BS-CS310": {
        "inheritance": (
            "Lecture 2 — Inheritance.\n"
            "A subclass inherits the fields and methods of its base class and may override them. "
            "An overridden method is selected at runtime based on the object's actual "
            "type, not the reference type. A frequent misconception: students assume the "
            "declared (reference) type decides which method runs. It does not — dynamic "
            "dispatch uses the real object."
        ),
    },
    "BS-DS200": {
        "conditional_probability": (
            "Lecture 2 — Conditional Probability.\n"
            "P(A|B) = P(A and B) / P(B). It measures the probability of A within the restricted "
            "world where B has occurred. A classic error is confusing P(A|B) with P(B|A); these "
            "are equal only in special cases. Bayes' theorem relates them: "
            "P(A|B) = P(B|A) P(A) / P(B)."
        ),
    },
}


def _seed_materials(db, course_id, uploader_id, key_to_concept, bs_id):
    from app.services.material_service import create_material

    for ckey, text in _MATERIALS.get(bs_id, {}).items():
        concept = key_to_concept.get(ckey)
        create_material(
            db,
            course_id=course_id,
            title=f"Lecture Notes — {concept.name if concept else ckey}",
            filename=f"{ckey}_notes.md",
            content_type="text/markdown",
            data=text.encode("utf-8"),
            concept_id=concept.id if concept else None,
            uploaded_by=uploader_id,
        )
    db.commit()


def ensure_platform_admin() -> None:
    """Idempotently provision the platform operator from env vars (runs every startup).

    Lets operators be created/promoted on hosts with no shell access (e.g. Render free
    tier): set PLATFORM_ADMIN_EMAIL (+ PLATFORM_ADMIN_PASSWORD on first create) and redeploy.
    Safe to run repeatedly — it never duplicates, and only sets the password when provided.
    """
    from app.core.config import settings

    email = (settings.platform_admin_email or "").strip().lower()
    if not email:
        return
    password = settings.platform_admin_password

    try:
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            if user:
                changed = False
                if not user.is_platform_admin:
                    user.is_platform_admin = True
                    changed = True
                if user.role != UserRole.admin:
                    user.role = UserRole.admin
                    changed = True
                if password:
                    user.hashed_password = hash_password(password)
                    changed = True
                if changed:
                    db.commit()
                    logger.info("Promoted %s to platform admin (env bootstrap).", email)
            elif password:
                db.add(User(
                    email=email, full_name="Platform Operator", role=UserRole.admin,
                    is_platform_admin=True, tenant_id=None,
                    hashed_password=hash_password(password),
                ))
                db.commit()
                logger.info("Created platform admin %s (env bootstrap).", email)
            else:
                logger.warning(
                    "PLATFORM_ADMIN_EMAIL=%s set but user missing and no "
                    "PLATFORM_ADMIN_PASSWORD provided; skipping.", email,
                )
    except Exception:  # noqa: BLE001 — never block app startup on bootstrap
        logger.exception("ensure_platform_admin failed; continuing startup.")


def seed(reset: bool = False, if_empty: bool = False) -> None:
    if reset:
        logger.info("Dropping and recreating all tables...")
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with SessionLocal() as db:
        if if_empty and db.scalar(select(User).limit(1)):
            logger.info("Database already populated; skipping seed (--if-empty).")
            return

        instructor = _get_or_create_user(
            db, "instructor@example.edu", "Dr. Alex Rivera", UserRole.instructor, "instructor123"
        )
        # Institution (IT) admin: configures AI & privacy and sees usage for their own
        # institution. Scoped to the tenant; NOT a platform operator.
        admin = _get_or_create_user(
            db, "admin@example.edu", "Institution Admin", UserRole.admin, "admin123"
        )
        admin.is_platform_admin = False
        # Platform operator (the LMS Bridge vendor): cross-tenant, sees leads + LTI
        # registrations across all institutions. Separate account from any institution admin.
        platform_admin = _get_or_create_user(
            db, "platform@lmsbridge.app", "Platform Operator", UserRole.admin, "platform123"
        )
        platform_admin.is_platform_admin = True
        platform_admin.tenant_id = None  # not tied to a single institution
        logger.info("Instructor:       %s / instructor123", instructor.email)
        logger.info("Institution admin: %s / admin123", admin.email)
        logger.info("Platform admin:    %s / platform123", platform_admin.email)

        # A default institution (tenant) — the institution admin configures BYO-AI + privacy on it.
        from app.models.tenant import Tenant
        tenant = db.scalar(select(Tenant).where(Tenant.slug == "demo-university"))
        if not tenant:
            tenant = Tenant(
                name="Demo University", slug="demo-university",
                subscription_status="active", plan="enterprise", seat_limit=5000,
            )
            db.add(tenant)
            db.flush()
        admin.tenant_id = tenant.id
        instructor.tenant_id = tenant.id

        for code, title, term, bs_id in COURSES:
            course = db.scalar(select(Course).where(Course.code == code, Course.term == term))
            if not course:
                course = Course(code=code, title=title, term=term,
                                brightspace_course_id=bs_id, tenant_id=tenant.id)
                db.add(course)
                db.flush()
            db.add(Enrollment(user_id=instructor.id, course_id=course.id, role=UserRole.instructor))

            key_to_concept: dict[str, Concept] = {}
            for key, name, desc, seq, _prereqs in CONCEPTS[bs_id]:
                concept = db.scalar(
                    select(Concept).where(Concept.course_id == course.id, Concept.key == key)
                )
                if not concept:
                    concept = Concept(
                        course_id=course.id, key=key, name=name, description=desc, sequence=seq,
                        common_misconceptions=(
                            f"Students often confuse {name.lower()} fundamentals."
                        ),
                    )
                    db.add(concept)
                    db.flush()
                key_to_concept[key] = concept
            # wire prerequisites
            for key, _n, _d, _s, prereqs in CONCEPTS[bs_id]:
                concept = key_to_concept[key]
                concept.prerequisites = [key_to_concept[p] for p in prereqs if p in key_to_concept]
            db.commit()

            # Sample course material -> grounds the AI remediation for early concepts.
            _seed_materials(db, course.id, instructor.id, key_to_concept, bs_id)

            # Run the Brightspace mock sync -> ingests results, builds mastery + remediation.
            summary = sync_course_results(
                db, course_id=course.id, course_external_id=bs_id
            )
            logger.info("Seeded %s: %s", code, summary)

        # Make one student login easy to remember.
        a_student = db.scalar(select(User).where(User.role == UserRole.student))
        if a_student:
            a_student.hashed_password = hash_password("student123")
            db.commit()
            logger.info("Sample student: %s / student123", a_student.email)

    logger.info("Seed complete.")


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="Seed LMS Bridge demo data")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables first")
    parser.add_argument("--if-empty", action="store_true", help="Only seed if DB has no users")
    args = parser.parse_args()
    seed(reset=args.reset, if_empty=args.if_empty)


if __name__ == "__main__":
    main()
