"""Shared FastAPI dependencies: DB session + authenticated user/role guards."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise credentials_error
    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise credentials_error
    return user


def require_role(*roles: UserRole):
    """Dependency factory that enforces the user holds one of the given roles."""

    def _guard(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this resource",
            )
        return user

    return _guard


require_instructor = require_role(UserRole.instructor, UserRole.admin)
require_student = require_role(UserRole.student, UserRole.instructor, UserRole.admin)


def require_platform_admin(user: User = Depends(get_current_user)) -> User:
    """Platform operator only — cross-tenant + sales surfaces.

    In `community` (single self-hosted institution) mode there is no separate platform
    operator: the institution admin runs everything, including their own LMS registration,
    so any admin qualifies. In `hosted` mode the `is_platform_admin` flag is required.
    """
    if settings.deployment_mode == "community":
        if user.role == UserRole.admin:
            return user
    elif user.role == UserRole.admin and user.is_platform_admin:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Platform-admin access required",
    )
