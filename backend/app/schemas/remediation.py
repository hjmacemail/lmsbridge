from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.enums import ActivityType, MasteryStatus, PedagogyStrategy, RemediationStatus
from app.schemas.common import ORMModel


class ActivityOut(ORMModel):
    id: int
    sequence: int
    activity_type: ActivityType
    prompt: str
    payload: dict | None = None


class RemediationModuleOut(ORMModel):
    id: int
    student_id: int
    course_id: int
    concept_id: int
    strategy: PedagogyStrategy
    status: RemediationStatus
    title: str
    rationale: str | None = None
    generated_by_model: str | None = None
    grounded_on: list[str] | None = None
    completed_at: datetime | None = None
    activities: list[ActivityOut] = []


class GenerateRemediationRequest(BaseModel):
    student_id: int
    concept_id: int
    trigger_result_id: int | None = None
    strategy: PedagogyStrategy | None = None


class SubmitResponseRequest(BaseModel):
    response_text: str


class ResponseFeedbackOut(ORMModel):
    id: int
    activity_id: int
    response_text: str
    is_correct: bool | None = None
    feedback: str | None = None
    resolves_misconception: bool | None = None


class TutorMessageOut(ORMModel):
    id: int
    sequence: int
    role: str  # "tutor" | "student"
    content: str
    choices: list[str] | None = None

    @field_validator("choices", mode="before")
    @classmethod
    def _parse_choices(cls, v):
        if isinstance(v, str):
            import json
            try:
                out = json.loads(v)
                return out if isinstance(out, list) else None
            except Exception:  # noqa: BLE001
                return None
        return v


class ClassBrief(BaseModel):
    """The AI Classroom Brief — real class numbers + a model-written summary and next action."""
    health_pct: int | None = None
    students_total: int
    needs_attention: int
    top_concept: str | None = None
    top_concept_mastery: int | None = None
    top_concept_affected: int | None = None
    top_misconception: str | None = None
    ai_sessions: int
    ai_completed: int
    not_started: int
    brief: str
    recommendation: str


class SessionEvidence(BaseModel):
    """The specific wrong answer that triggered this session (drives the 'why you're here' card)."""
    question: str | None = None
    chosen: str | None = None
    correct: str | None = None
    misconception: str | None = None


class SessionState(BaseModel):
    module_id: int
    title: str
    concept_id: int
    status: RemediationStatus
    rationale: str | None = None
    grounded_on: list[str] | None = None
    messages: list[TutorMessageOut] = []
    # Structured learning context so the UI can show a real goal, plan, and misconception
    # (not just the tutor's free-text opening).
    concept_name: str | None = None
    goal: str | None = None
    objectives: list[str] = []
    mastery_score: float | None = None
    focus_misconception: str | None = None
    evidence: SessionEvidence | None = None


class SessionMessageRequest(BaseModel):
    text: str
    lang: str | None = None  # locale code (e.g. "ar", "fr") — tutor replies in this language


class SessionTurnOut(BaseModel):
    reply: str
    complete: bool
    status: RemediationStatus
    choices: list[str] | None = None


class MasteryOut(ORMModel):
    concept_id: int
    concept_key: str | None = None
    concept_name: str | None = None
    mastery_score: float
    status: MasteryStatus
    evidence_count: int


class StudentDashboard(BaseModel):
    student_id: int
    full_name: str
    masteries: list[MasteryOut] = []
    open_modules: list[RemediationModuleOut] = []
    completed_modules: int = 0


class ConceptRisk(BaseModel):
    concept_id: int
    concept_key: str
    concept_name: str
    avg_mastery: float
    at_risk_count: int
    total_students: int


class InstructorAnalytics(BaseModel):
    course_id: int
    course_title: str
    enrolled_students: int
    concept_risks: list[ConceptRisk] = []
    modules_generated: int = 0
    modules_completed: int = 0
