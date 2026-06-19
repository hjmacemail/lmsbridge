"""Licensing & entitlement enforcement.

Two delivery models are supported (see config):

* **SaaS (default).** Each institution is a `Tenant`; its `subscription_status`,
  `license_expires_at`, and `seat_limit` are enforced on every LTI launch. The platform
  operator (or a Stripe webhook) flips these.
* **Self-hosted.** When `LICENSE_PUBLIC_KEY` is configured, the install requires a signed
  `LICENSE_KEY` token (a JWT signed by the vendor's private key), validated offline at
  startup against the bundled public key. No valid token → the install is unlicensed and
  launches are blocked. Seat/expiry come from the signed token.

Mint a self-hosted license with `python -m app.scripts.mint_license` (vendor-side only).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.enums import UserRole
from app.models.tenant import Tenant
from app.models.user import User

logger = get_logger("license")

LICENSE_ISSUER = "lms-bridge-licensing"
_ALLOWED_STATUSES = ("active", "trial")


@dataclass
class Decision:
    allowed: bool
    reason: str      # machine code, e.g. "ok" | "subscription_suspended" | "seat_limit_reached"
    detail: str      # human-friendly sentence for the blocked screen


@dataclass
class SelfHostedState:
    ok: bool
    reason: str
    detail: str
    customer: str | None = None
    plan: str | None = None
    seats: int | None = None
    expires_at: str | None = None


_self_hosted: SelfHostedState | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --------------------------------------------------------------------------- #
# Self-hosted signed-license handling
# --------------------------------------------------------------------------- #
def enforcement_active() -> bool:
    """Whether launches are license-gated at all.

    Off in `community` mode (the free, self-hosted default) and off when explicitly
    disabled — so a self-hoster's students are never blocked.
    """
    return settings.deployment_mode != "community" and not settings.license_enforcement_disabled


def self_hosted_mode() -> bool:
    """True when this deployment is gated by a signed license file."""
    return bool(settings.license_public_key)


def verify_license_token(token: str, public_key_pem: str) -> dict:
    """Verify a signed license JWT and return its claims. Raises JWTError on failure."""
    return jwt.decode(
        token, public_key_pem, algorithms=["RS256"],
        issuer=LICENSE_ISSUER, options={"verify_aud": False},
    )


def load_self_hosted_license() -> SelfHostedState:
    """Validate LICENSE_KEY against LICENSE_PUBLIC_KEY and cache the result (idempotent)."""
    global _self_hosted
    if not self_hosted_mode():
        _self_hosted = SelfHostedState(True, "saas", "SaaS mode — per-tenant subscriptions.")
        return _self_hosted

    token = settings.license_key
    if not token:
        _self_hosted = SelfHostedState(
            False, "license_missing",
            "No license key installed. Set LICENSE_KEY to the signed token issued to you.",
        )
        logger.warning("Self-hosted mode but LICENSE_KEY is not set; install is unlicensed.")
        return _self_hosted

    try:
        claims = verify_license_token(token, settings.license_public_key)  # type: ignore[arg-type]
    except ExpiredSignatureError:
        _self_hosted = SelfHostedState(
            False, "license_expired", "Your LMS Bridge license has expired. Please renew.")
        logger.warning("Self-hosted license expired.")
        return _self_hosted
    except JWTError as e:
        _self_hosted = SelfHostedState(
            False, "license_invalid", "The installed license key is invalid.")
        logger.warning("Self-hosted license invalid: %s", e)
        return _self_hosted

    exp = claims.get("exp")
    _self_hosted = SelfHostedState(
        ok=True, reason="ok", detail="Licensed.",
        customer=claims.get("sub"), plan=claims.get("plan"),
        seats=claims.get("seats"),
        expires_at=(datetime.fromtimestamp(exp, tz=timezone.utc).isoformat() if exp else None),
    )
    logger.info(
        "Self-hosted license OK: customer=%s plan=%s seats=%s",
        _self_hosted.customer, _self_hosted.plan, _self_hosted.seats,
    )
    return _self_hosted


def self_hosted_state() -> SelfHostedState:
    if _self_hosted is None:
        return load_self_hosted_license()
    return _self_hosted


# --------------------------------------------------------------------------- #
# Seat accounting
# --------------------------------------------------------------------------- #
def count_students(db: Session, tenant: Tenant) -> int:
    return db.scalar(
        select(func.count(User.id)).where(
            User.tenant_id == tenant.id, User.role == UserRole.student
        )
    ) or 0


def _seat_allows(db: Session, tenant: Tenant, user: User, seat_limit: int) -> bool:
    """Allow the first `seat_limit` students (by id) — only the overflow is blocked."""
    student_ids = list(db.scalars(
        select(User.id).where(
            User.tenant_id == tenant.id, User.role == UserRole.student
        ).order_by(User.id)
    ).all())
    return user.id in set(student_ids[:seat_limit])


# --------------------------------------------------------------------------- #
# Launch authorization
# --------------------------------------------------------------------------- #
def _saas_subscription_ok(tenant: Tenant) -> Decision:
    status = (tenant.subscription_status or "").lower()
    if status not in _ALLOWED_STATUSES:
        return Decision(
            False, f"subscription_{status or 'unknown'}",
            f"This institution's LMS Bridge subscription is {status or 'not active'}.",
        )
    exp = tenant.license_expires_at
    if exp is not None:
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < _now():
            return Decision(
                False, "expired",
                "This institution's LMS Bridge license has expired.",
            )
    return Decision(True, "ok", "")


def authorize_launch(db: Session, tenant: Tenant, user: User) -> Decision:
    """Decide whether this user's launch is permitted under the current license."""
    if not enforcement_active():
        return Decision(True, "ok", "")

    if self_hosted_mode():
        st = self_hosted_state()
        if not st.ok:
            return Decision(False, st.reason, st.detail)
        seat_limit = st.seats
    else:
        sub = _saas_subscription_ok(tenant)
        if not sub.allowed:
            return sub
        seat_limit = tenant.seat_limit

    if user.role == UserRole.student and seat_limit is not None:
        if not _seat_allows(db, tenant, user, seat_limit):
            return Decision(
                False, "seat_limit_reached",
                f"This institution has reached its licensed seat limit ({seat_limit} "
                "students). Ask your administrator to add seats.",
            )
    return Decision(True, "ok", "")


# --------------------------------------------------------------------------- #
# UI summary
# --------------------------------------------------------------------------- #
def license_summary(db: Session, tenant: Tenant | None) -> dict:
    """Compact license state for the console (mode + self-hosted status + tenant snapshot)."""
    out: dict = {
        "deployment_mode": settings.deployment_mode,
        "enforcement_active": enforcement_active(),
        "mode": "self_hosted" if self_hosted_mode() else "saas",
        "enforcement_disabled": settings.license_enforcement_disabled,
    }
    if self_hosted_mode():
        st = self_hosted_state()
        out["self_hosted"] = {
            "ok": st.ok, "reason": st.reason, "detail": st.detail,
            "customer": st.customer, "plan": st.plan, "seats": st.seats,
            "expires_at": st.expires_at,
        }
    if tenant is not None:
        exp = tenant.license_expires_at
        out["tenant"] = {
            "subscription_status": tenant.subscription_status,
            "plan": tenant.plan,
            "seat_limit": tenant.seat_limit,
            "seats_used": count_students(db, tenant),
            "license_expires_at": exp.isoformat() if exp else None,
        }
    return out
