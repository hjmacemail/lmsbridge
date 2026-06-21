from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class CanvasImportRequest(BaseModel):
    course_id: int
    base_url: str = Field(..., description="Canvas host, e.g. https://school.instructure.com")
    access_token: str = Field(..., description="Canvas access token (Account > Settings)")
    canvas_course_id: str = Field(..., description="Numeric Canvas course id (from course URL)")


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
