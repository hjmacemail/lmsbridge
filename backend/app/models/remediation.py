from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import ActivityType, PedagogyStrategy, RemediationStatus


class RemediationModule(Base, TimestampMixin):
    """A tailored, multi-activity remediation unit for one student + concept."""

    __tablename__ = "remediation_modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"))
    concept_id: Mapped[int] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"))
    trigger_result_id: Mapped[int | None] = mapped_column(
        ForeignKey("assessment_results.id", ondelete="SET NULL")
    )
    strategy: Mapped[PedagogyStrategy] = mapped_column(
        SAEnum(PedagogyStrategy), default=PedagogyStrategy.socratic_scaffolding
    )
    status: Mapped[RemediationStatus] = mapped_column(
        SAEnum(RemediationStatus), default=RemediationStatus.pending
    )
    title: Mapped[str] = mapped_column(String(255))
    rationale: Mapped[str | None] = mapped_column(Text)  # why this was triggered
    generated_by_model: Mapped[str | None] = mapped_column(String(128))
    # Titles of instructor materials used to ground generation (transparency).
    grounded_on: Mapped[list | None] = mapped_column(JSON)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    student: Mapped[User] = relationship()  # noqa: F821
    concept: Mapped[Concept] = relationship()  # noqa: F821
    # Activities act as the tutor's internal session plan / learning checkpoints.
    activities: Mapped[list[RemediationActivity]] = relationship(
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="RemediationActivity.sequence",
    )
    # The live, turn-by-turn transcript of the interactive tutoring session.
    messages: Mapped[list[TutorMessage]] = relationship(  # noqa: F821
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="TutorMessage.sequence",
    )


class RemediationActivity(Base, TimestampMixin):
    __tablename__ = "remediation_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("remediation_modules.id", ondelete="CASCADE"))
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    activity_type: Mapped[ActivityType] = mapped_column(SAEnum(ActivityType))
    prompt: Mapped[str] = mapped_column(Text)
    # Optional structured payload: hints, expected_focus, starter_code, choices, etc.
    payload: Mapped[dict | None] = mapped_column(JSON)

    module: Mapped[RemediationModule] = relationship(back_populates="activities")
    responses: Mapped[list[StudentResponse]] = relationship(
        back_populates="activity", cascade="all, delete-orphan"
    )


class TutorMessage(Base, TimestampMixin):
    """One turn in the interactive AI-tutor session for a remediation module."""

    __tablename__ = "tutor_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_id: Mapped[int] = mapped_column(ForeignKey("remediation_modules.id", ondelete="CASCADE"))
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    role: Mapped[str] = mapped_column(String(16))  # "tutor" | "student"
    content: Mapped[str] = mapped_column(Text)

    module: Mapped[RemediationModule] = relationship(back_populates="messages")


class StudentResponse(Base, TimestampMixin):
    """A student's attempt at a remediation activity + AI-generated formative feedback."""

    __tablename__ = "student_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    activity_id: Mapped[int] = mapped_column(
        ForeignKey("remediation_activities.id", ondelete="CASCADE")
    )
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    response_text: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    feedback: Mapped[str | None] = mapped_column(Text)
    # Did the AI judge the underlying misconception resolved by this response?
    resolves_misconception: Mapped[bool | None] = mapped_column(Boolean)

    activity: Mapped[RemediationActivity] = relationship(back_populates="responses")
