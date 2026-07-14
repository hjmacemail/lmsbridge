from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import MasteryStatus


class ConceptMastery(Base, TimestampMixin):
    """Running estimate of a student's mastery of a concept."""

    __tablename__ = "concept_mastery"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"))
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0..1
    status: Mapped[MasteryStatus] = mapped_column(
        SAEnum(MasteryStatus), default=MasteryStatus.developing
    )
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    last_evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student: Mapped[User] = relationship()  # noqa: F821
    concept: Mapped[Concept] = relationship()  # noqa: F821

    __table_args__ = (UniqueConstraint("student_id", "concept_id", name="uq_mastery"),)


class MasterySnapshot(Base, TimestampMixin):
    """Daily class-average mastery per concept, so the dashboard can show real trends over time."""

    __tablename__ = "mastery_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"))
    avg_mastery: Mapped[float] = mapped_column(Float, default=0.0)
    at_risk_count: Mapped[int] = mapped_column(Integer, default=0)
    taken_on: Mapped[date] = mapped_column(Date, index=True)

    __table_args__ = (
        UniqueConstraint("course_id", "concept_id", "taken_on", name="uq_snapshot_day"),
    )
