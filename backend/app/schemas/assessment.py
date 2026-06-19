from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AssessmentType
from app.schemas.common import ORMModel


class AssessmentOut(ORMModel):
    id: int
    course_id: int
    title: str
    type: AssessmentType
    max_score: float
    available_at: datetime | None = None
    adaptive_enabled: bool = True


class AdaptiveToggle(BaseModel):
    enabled: bool


class ItemScore(BaseModel):
    concept_key: str
    earned: float
    max: float
    question_id: int | None = None


class ResultIngest(BaseModel):
    """Payload to ingest a single student's result (from Brightspace or manual)."""
    assessment_id: int
    student_external_id: str
    score: float  # normalized 0..1
    item_scores: list[ItemScore] = []
    rubric_feedback: str | None = None


class ResultOut(ORMModel):
    id: int
    assessment_id: int
    student_id: int
    score: float
    rubric_feedback: str | None = None
