from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class CourseMaterial(Base, TimestampMixin):
    """Instructor-uploaded course material used to ground AI remediation.

    The raw bytes are kept for the reference library (download); `extracted_text`
    holds the parsed text that the remediation engine injects as grounding context.
    """

    __tablename__ = "course_materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    # Optional concept tag — if set, this material grounds that concept specifically.
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id", ondelete="SET NULL"))
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    # What kind of resource this is: file | note | code | link (drives how Sage renders it).
    kind: Mapped[str] = mapped_column(String(16), default="file", server_default="file")
    # Programming language for code snippets (e.g. "python"), optional.
    language: Mapped[str | None] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    content: Mapped[bytes | None] = mapped_column(LargeBinary)  # raw file for download

    course: Mapped[Course] = relationship()  # noqa: F821
    concept: Mapped[Concept | None] = relationship()  # noqa: F821
