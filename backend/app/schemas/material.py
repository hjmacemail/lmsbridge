from __future__ import annotations

from datetime import datetime

from app.schemas.common import ORMModel


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
