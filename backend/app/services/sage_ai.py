"""Sage's Socratic AI: a guiding reply + misconception label for a posted question.

Reuses the platform's provider-agnostic LLM layer. The AI never hands over the final
answer — it nudges the student's thinking and names the likely underlying misconception
(which powers the instructor insights dashboard).
"""
from __future__ import annotations

from app.core.logging import get_logger
from app.llm.base import LLMMessage
from app.llm.factory import get_llm_provider
from app.llm.providers.mock import extract_json

logger = get_logger("sage.ai")

_SYSTEM = (
    "You are Sage, a Socratic AI teaching assistant on a class Q&A board. "
    "A student posted a question. Help them LEARN rather than handing over the answer. "
    "Write ONE short, encouraging reply (2-4 sentences) that asks a guiding question or gives a "
    "hint to move their thinking forward, using sound pedagogy (retrieval practice, Socratic "
    "scaffolding). Also name the single most likely underlying misconception in a few words, or "
    'null if none. Respond ONLY as JSON: {"reply": string, "misconception": string|null}.'
)

_FALLBACK = (
    "Great question. Before I weigh in — what have you tried so far, and which specific step is "
    "tripping you up? Walk me through your reasoning and I'll help you find the gap."
)


def socratic_reply(
    title: str, body: str = "", subject: str | None = None
) -> tuple[str, str | None]:
    """Return (reply_text, misconception_label_or_None) for a posted question."""
    messages = [
        LLMMessage("system", f"Subject: {subject or 'this course'}.\n{_SYSTEM}"),
        LLMMessage("user", f"Question title: {title}\n\nDetails: {body or '(none)'}"),
    ]
    try:
        resp = get_llm_provider().complete(messages, json_mode=True)
        data = extract_json(resp.text) or {}
    except Exception as e:  # noqa: BLE001 — AI must never break a post
        logger.warning("Sage AI reply failed: %s", e)
        data = {}

    reply = (data.get("reply") or "").strip() or _FALLBACK
    mis = data.get("misconception")
    misconception = mis.strip() if isinstance(mis, str) and mis.strip() else None
    return reply, misconception
