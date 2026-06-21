from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text, true
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import AssessmentType


class Assessment(Base, TimestampMixin):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    brightspace_assessment_id: Mapped[str | None] = mapped_column(String(128), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[AssessmentType] = mapped_column(SAEnum(AssessmentType))
    max_score: Mapped[float] = mapped_column(Float, default=100.0)
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # When False, this assessment's feedback is recorded but NOT used to update
    # mastery or trigger adaptive remediation (admin/instructor controlled).
    adaptive_enabled: Mapped[bool] = mapped_column(default=True, server_default=true())

    course: Mapped[Course] = relationship()  # noqa: F821
    questions: Mapped[list[Question]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    results: Mapped[list[AssessmentResult]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class Question(Base, TimestampMixin):
    """A question/item on an assessment, tagged to a concept for diagnosis."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"))
    concept_id: Mapped[int | None] = mapped_column(ForeignKey("concepts.id", ondelete="SET NULL"))
    prompt: Mapped[str] = mapped_column(Text)
    max_points: Mapped[float] = mapped_column(Float, default=1.0)
    # Authored MCQ content (Sage quizzes): list of choice strings + the correct choice text.
    choices: Mapped[list | None] = mapped_column(JSON)
    correct_answer: Mapped[str | None] = mapped_column(Text)

    assessment: Mapped[Assessment] = relationship(back_populates="questions")
    concept: Mapped[Concept | None] = relationship()  # noqa: F821


class AssessmentResult(Base, TimestampMixin):
    """A student's outcome on an assessment, with per-question payload from the LMS."""

    __tablename__ = "assessment_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    score: Mapped[float] = mapped_column(Float)  # normalized 0..1
    # Raw per-question detail: [{"question_id":..,"concept_key":..,"earned":..,"max":..}]
    item_scores: Mapped[list | None] = mapped_column(JSON)
    rubric_feedback: Mapped[str | None] = mapped_column(Text)
    # Rubric-level breakdown from the LMS:
    # [{"criterion":..,"concept_key":..,"level":..,"points":..,"max_points":..,"comment":..}]
    rubric_criteria: Mapped[list | None] = mapped_column(JSON)
    # Engagement signals the LMS commonly exposes.
    attempts: Mapped[int | None] = mapped_column()
    time_on_task_minutes: Mapped[float | None] = mapped_column(Float)
    submitted_late: Mapped[bool | None] = mapped_column()
    ingested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    assessment: Mapped[Assessment] = relationship(back_populates="results")
    student: Mapped[User] = relationship()  # noqa: F821
