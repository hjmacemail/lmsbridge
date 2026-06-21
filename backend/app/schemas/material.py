from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class LmsImportRequest(BaseModel):
    course_id: int
    provider: str = Field(..., description="canvas | moodle | brightspace")
    base_url: str = Field(..., description="LMS host, e.g. https://school.instructure.com")
    access_token: str = Field(..., description="LMS API token / OAuth2 bearer token")
    lms_course_id: str = Field(..., description="Provider course/org-unit id")


class MaterialOut(ORMModel):
    id: int
    course_id: int
    concept_id: int | None = None
    title: str
    filename: str
    content_type: str
    size_bytes: int
    has_text: bool = False
    created_at: datetime


class MaterialDetail(MaterialOut):
    text_preview: str | None = None
