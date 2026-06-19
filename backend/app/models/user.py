from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String, false
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.student)
    # Identifier in the source LMS (Brightspace user id)
    external_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), index=True
    )
    # Platform operator (sees all tenants + sales leads). An `admin` WITHOUT this flag is an
    # institution admin, scoped to their own tenant. Never granted via LTI.
    is_platform_admin: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )

    enrollments: Mapped[list[Enrollment]] = relationship(  # noqa: F821
        back_populates="user", cascade="all, delete-orphan"
    )
