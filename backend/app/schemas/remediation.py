from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

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


class SessionState(BaseModel):
    module_id: int
    title: str
    concept_id: int
    status: RemediationStatus
    rationale: str | None = None
    grounded_on: list[str] | None = None
    messages: list[TutorMessageOut] = []


class SessionMessageRequest(BaseModel):
    text: str
    lang: str | None = None  # locale code (e.g. "ar", "fr") — tutor replies in this language


class SessionTurnOut(BaseModel):
    reply: str
    complete: bool
    status: RemediationStatus


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
