from __future__ import annotations

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import UserRole


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    term: Mapped[str] = mapped_column(String(64), nullable=False)
    brightspace_course_id: Mapped[str | None] = mapped_column(String(128), index=True)
    # LTI NRPS (Names & Role Provisioning) context membership URL, captured at launch so the
    # full course roster can be (re)synced from the LMS without waiting for each student to launch.
    lti_memberships_url: Mapped[str | None] = mapped_column(String(1024))
    # LTI AGS (Assignment & Grade Services) line-items URL, captured at launch so the course's
    # assessments/gradebook columns can be (re)synced from the LMS automatically.
    lti_lineitems_url: Mapped[str | None] = mapped_column(String(1024))
    tenant_id: Mapped[int | None] = mapped_column(
        ForeignKey("tenants.id", ondelete="SET NULL"), index=True
    )

    enrollments: Mapped[list[Enrollment]] = relationship(  # noqa: F821
        back_populates="course", cascade="all, delete-orphan"
    )
    concepts: Mapped[list[Concept]] = relationship(  # noqa: F821
        back_populates="course", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("code", "term", name="uq_course_code_term"),)


class Enrollment(Base, TimestampMixin):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.student)

    user: Mapped[User] = relationship(back_populates="enrollments")  # noqa: F821
    course: Mapped[Course] = relationship(back_populates="enrollments")

    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_enrollment"),)
