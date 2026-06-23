from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import Token, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


class DemoLoginRequest(BaseModel):
    role: str = "student"  # "student" | "instructor"


@router.post("/login", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> Token:
    # OAuth2 form uses 'username' — we treat it as email.
    user = db.scalar(select(User).where(User.email == form.username))
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(
        access_token=token, role=user.role, user_id=user.id, full_name=user.full_name,
        is_platform_admin=user.is_platform_admin,
    )


@router.post("/demo-login", response_model=Token)
def demo_login(payload: DemoLoginRequest, db: Session = Depends(get_db)) -> Token:
    """Password-less sign-in as the seeded demo student/instructor (for the public demo).

    Returns the demo account for the requested role. Disabled when `demo_login_enabled` is
    false (set that on a real institutional deployment). Never returns an admin account.
    """
    if not settings.demo_login_enabled:
        raise HTTPException(status_code=404, detail="Demo login is disabled")
    role = UserRole.instructor if payload.role == "instructor" else UserRole.student
    user = db.scalar(
        select(User).where(User.role == role).order_by(User.id)
    )
    if not user:
        raise HTTPException(status_code=404, detail="No seeded demo user available")

    # Self-heal: if the shared demo has been emptied (e.g. visitors completed everything, or a
    # prior reset cleared it), regenerate the rich starting state so nobody lands on an empty demo.
    from app.models.enums import RemediationStatus
    from app.models.remediation import RemediationModule
    has_open = db.scalar(
        select(func.count(RemediationModule.id)).where(
            RemediationModule.status.in_(
                [RemediationStatus.pending, RemediationStatus.in_progress]))
    ) or 0
    if has_open == 0:
        from app.services.demo_service import reset_demo_data
        try:
            reset_demo_data(db)
        except Exception:  # noqa: BLE001 — never block demo sign-in on a regeneration hiccup
            db.rollback()
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(
        access_token=token, role=user.role, user_id=user.id, full_name=user.full_name,
        is_platform_admin=user.is_platform_admin,
    )


@router.post("/demo-reset")
def demo_reset(db: Session = Depends(get_db)) -> dict:
    """Restore the seeded demo data to its pristine starting state (public-demo affordance)."""
    if not settings.demo_login_enabled:
        raise HTTPException(status_code=404, detail="Demo is disabled")
    from app.services.demo_service import reset_demo_data
    return reset_demo_data(db)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
