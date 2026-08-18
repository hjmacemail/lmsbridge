"""Sage standalone-course extras: instructor announcements and assignments."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class SageAnnouncement(Base, TimestampMixin):
    __tablename__ = "sage_announcements"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")


class SageAssignment(Base, TimestampMixin):
    """An instructor-posted assignment students submit a written response to and are graded on."""

    __tablename__ = "sage_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, default="")  # Markdown
    points: Mapped[int] = mapped_column(Integer, default=100)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SageSubmission(Base, TimestampMixin):
    """A student's response to an assignment, plus the instructor's grade + feedback.

    One row per (assignment, student); resubmitting before grading overwrites the body.
    """

    __tablename__ = "sage_submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_sage_submission"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("sage_assignments.id", ondelete="CASCADE"), index=True
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    body: Mapped[str] = mapped_column(Text, default="")  # Markdown
    # Optional file attachment (stored inline, like course materials).
    file_name: Mapped[str | None] = mapped_column(String(255))
    content_type: Mapped[str | None] = mapped_column(String(128))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    file_content: Mapped[bytes | None] = mapped_column(LargeBinary)
    grade: Mapped[float | None] = mapped_column(Float)  # points awarded, out of assignment.points
    feedback: Mapped[str] = mapped_column(Text, default="")
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    graded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
