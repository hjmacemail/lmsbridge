"""Store course material and select relevant excerpts to ground remediation."""
from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.concept import Concept
from app.models.material import CourseMaterial
from app.services.extraction_service import extract_text

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


def create_material(
    db: Session,
    *,
    course_id: int,
    title: str,
    filename: str,
    content_type: str,
    data: bytes,
    concept_id: int | None = None,
    uploaded_by: int | None = None,
) -> CourseMaterial:
    text = extract_text(filename, content_type, data)
    material = CourseMaterial(
        course_id=course_id,
        concept_id=concept_id,
        uploaded_by=uploaded_by,
        title=title or filename,
        filename=filename,
        content_type=content_type or "application/octet-stream",
        size_bytes=len(data),
        extracted_text=text or None,
        content=data,
    )
    db.add(material)
    db.flush()
    return material


def _score_overlap(text: str, terms: list[str]) -> int:
    low = text.lower()
    return sum(low.count(t) for t in terms if t)


def grounding_excerpts(
    db: Session, *, course_id: int, concept: Concept, max_chars: int = 1500, max_sources: int = 3
) -> list[dict]:
    """Return the most relevant material excerpts for a concept, for prompt grounding.

    Selection is intentionally simple and explainable: materials explicitly tagged to
    the concept rank first, then keyword overlap with the concept key/name. Each excerpt
    is the densest matching window of the material's extracted text.
    """
    materials = db.scalars(
        select(CourseMaterial).where(
            CourseMaterial.course_id == course_id,
            CourseMaterial.extracted_text.is_not(None),
        )
    ).all()
    if not materials:
        return []

    terms = [concept.key.replace("_", " ").lower(), (concept.name or "").lower()]
    terms += [w for w in re.split(r"\W+", concept.name or "") if len(w) > 3]

    ranked: list[tuple[float, CourseMaterial]] = []
    for m in materials:
        tag_bonus = 100 if m.concept_id == concept.id else 0
        score = tag_bonus + _score_overlap(m.extracted_text or "", terms)
        if score > 0:
            ranked.append((score, m))
    ranked.sort(key=lambda x: x[0], reverse=True)

    excerpts: list[dict] = []
    for _score, m in ranked[:max_sources]:
        excerpts.append({
            "title": m.title,
            "excerpt": _best_window(m.extracted_text or "", terms, max_chars),
        })
    return excerpts


def _best_window(text: str, terms: list[str], width: int) -> str:
    """Return the window of `text` (length ~width) richest in the search terms."""
    if len(text) <= width:
        return text
    low = text.lower()
    best_pos, best_hits = 0, -1
    step = max(1, width // 2)
    for start in range(0, len(text) - width + 1, step):
        window = low[start:start + width]
        hits = sum(window.count(t) for t in terms if t)
        if hits > best_hits:
            best_hits, best_pos = hits, start
    snippet = text[best_pos:best_pos + width].strip()
    return ("…" if best_pos > 0 else "") + snippet + ("…" if best_pos + width < len(text) else "")
