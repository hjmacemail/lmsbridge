from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AssessmentType, RemediationStatus
from app.schemas.remediation import MasteryOut


class RosterEntry(BaseModel):
    student_id: int
    full_name: str
    email: str
    avg_mastery: float
    at_risk_concepts: int
    open_modules: int
    completed_modules: int


class ResultDetail(BaseModel):
    id: int
    assessment_id: int
    assessment_title: str
    assessment_type: AssessmentType
    score: float
    attempts: int | None = None
    time_on_task_minutes: float | None = None
    submitted_late: bool | None = None
    rubric_feedback: str | None = None
    item_scores: list[dict] = []
    rubric_criteria: list[dict] = []
    created_at: datetime


class StudentDetail(BaseModel):
    student_id: int
    full_name: str
    email: str
    masteries: list[MasteryOut] = []
    results: list[ResultDetail] = []
    modules: list[ModuleSummary] = []


class ModuleSummary(BaseModel):
    id: int
    concept_id: int
    concept_name: str | None = None
    title: str
    status: RemediationStatus
    strategy: str
    grounded_on: list[str] | None = None
    activity_count: int = 0
    response_count: int = 0
    created_at: datetime


class InstitutionCourseRow(BaseModel):
    course_id: int
    code: str
    title: str
    students: int
    modules_completed: int
    avg_mastery: float


class InstitutionUsage(BaseModel):
    """Institution-wide adoption metrics for the IT/ops admin.

    Deliberately aggregate-only: no individual student names, scores, or answers — that
    academic detail belongs to instructors, not the institution administrator.
    """

    tenant_name: str
    lms_connected: bool
    courses: int
    students: int
    instructors: int
    sessions_started: int
    modules_generated: int
    modules_completed: int
    completion_rate: float
    course_rows: list[InstitutionCourseRow] = []


class ConceptStat(BaseModel):
    concept_key: str
    concept_name: str
    avg: float
    n: int


class AssessmentBreakdown(BaseModel):
    assessment_id: int
    title: str
    type: AssessmentType
    adaptive_enabled: bool = True
    submissions: int
    avg_score: float
    concept_stats: list[ConceptStat] = []
    sample_rubric_feedback: list[str] = []


class ResponseDetail(BaseModel):
    id: int
    response_text: str
    is_correct: bool | None = None
    resolves_misconception: bool | None = None
    feedback: str | None = None


class ActivityWithResponses(BaseModel):
    id: int
    sequence: int
    activity_type: str
    prompt: str
    responses: list[ResponseDetail] = []


class TranscriptTurn(BaseModel):
    role: str
    content: str


class ModuleWithStudent(BaseModel):
    id: int
    student_id: int
    student_name: str
    concept_name: str | None = None
    title: str
    status: RemediationStatus
    strategy: str
    rationale: str | None = None
    grounded_on: list[str] | None = None
    created_at: datetime
    activities: list[ActivityWithResponses] = []
    transcript: list[TranscriptTurn] = []


StudentDetail.model_rebuild()
