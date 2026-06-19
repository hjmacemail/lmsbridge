from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

# Self-referential prerequisite graph: a concept depends on prerequisite concepts.
concept_prerequisites = Table(
    "concept_prerequisites",
    Base.metadata,
    Column("concept_id", ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
    Column("prerequisite_id", ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True),
)


class Concept(Base, TimestampMixin):
    """A learning objective / concept within a course (e.g. 'binary_arithmetic')."""

    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Free-text catalogue of common misconceptions, guides the LLM diagnosis.
    common_misconceptions: Mapped[str | None] = mapped_column(Text)
    # Ordering within the course sequence (lower = earlier / more foundational).
    sequence: Mapped[int] = mapped_column(default=0)

    course: Mapped[Course] = relationship(back_populates="concepts")  # noqa: F821

    prerequisites: Mapped[list[Concept]] = relationship(
        "Concept",
        secondary=concept_prerequisites,
        primaryjoin=id == concept_prerequisites.c.concept_id,
        secondaryjoin=id == concept_prerequisites.c.prerequisite_id,
        backref="dependents",
    )

    __table_args__ = (UniqueConstraint("course_id", "key", name="uq_concept_course_key"),)
