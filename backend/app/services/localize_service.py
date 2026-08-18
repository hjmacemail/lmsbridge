"""Localize short server-side domain strings (seeded misconception text, etc.) into the user's
language on demand.

The static UI is translated on the client; a few strings, though, live in the data layer
(e.g. a seeded misconception like "Forgets that zero is a representable value"). When a
non-English language is active we ask the configured model to translate them, with a hard
fallback to the original English if anything goes wrong — this must never break a request.
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.llm.base import LLMMessage
from app.llm.providers.mock import extract_json
from app.llm.tenant_factory import resolve_provider
from app.pedagogy.prompts import language_name

logger = get_logger("localize")


def localize_texts(
    db: Session, course_id: int | None, texts: list[str], lang: str | None
) -> list[str]:
    """Translate `texts` into `lang`. Returns the originals unchanged for English/unknown
    locales, empty input, or any failure (length mismatch, parse error, no model)."""
    lname = language_name(lang)
    if not lname or not texts:
        return texts
    # Preserve empties; only translate the non-empty ones.
    idx = [i for i, s in enumerate(texts) if s and s.strip()]
    if not idx:
        return texts
    try:
        llm = resolve_provider(db, course_id=course_id)
        payload = json.dumps([texts[i] for i in idx], ensure_ascii=False)
        system = (
            f"You are a translator. Translate each string in the given JSON array into natural, "
            f"fluent {lname}. Preserve meaning and keep well-known technical terms recognizable. "
            'Respond with ONLY a JSON object {"items": ["...", ...]} containing exactly the same '
            "number of items, in the same order. No prose, no code fences."
        )
        resp = llm.complete([LLMMessage("system", system), LLMMessage("user", payload)],
                            json_mode=True)
        items = extract_json(resp.text).get("items")
        if isinstance(items, list) and len(items) == len(idx):
            out = list(texts)
            for k, i in enumerate(idx):
                val = str(items[k]).strip() if items[k] is not None else ""
                out[i] = val or texts[i]
            return out
    except Exception as e:  # noqa: BLE001 — localization is best-effort; never fail the request.
        logger.info("localize_texts fell back to source (%s): %s", lname, e)
    return texts
