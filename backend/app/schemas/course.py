from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AssessmentType
from app.schemas.common import ORMModel


class ConceptOut(ORMModel):
    id: int
    key: str
    name: str
    description: str | None = None
    sequence: int
    common_misconceptions: str | None = None
    prerequisite_keys: list[str] = []


class CourseOut(ORMModel):
    id: int
    code: str
    title: str
    term: str
    brightspace_course_id: str | None = None


class CourseDetail(CourseOut):
    concepts: list[ConceptOut] = []


# ---- Manual course/concept/assessment management (for pilots without an LMS) ----

class CourseCreate(BaseModel):
    code: str
    title: str
    term: str = "2026SP"


class CourseUpdate(BaseModel):
    code: str | None = None
    title: str | None = None
    term: str | None = None


class ConceptCreate(BaseModel):
    key: str
    name: str
    description: str | None = None
    sequence: int = 0
    common_misconceptions: str | None = None
    prerequisite_keys: list[str] = []


class ConceptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sequence: int | None = None
    common_misconceptions: str | None = None
    prerequisite_keys: list[str] | None = None


class AssessmentCreate(BaseModel):
    title: str
    type: AssessmentType = AssessmentType.quiz
    max_score: float = 100.0
    available_at: datetime | None = None
