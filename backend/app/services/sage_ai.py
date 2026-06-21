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


_PRACTICE_SYSTEM = (
    "You are Sage, an AI tutor. Generate a SHORT retrieval-practice set (3 items) to help a "
    "student overcome a specific misconception. Each item has a focused question, the correct "
    "answer, and a one-sentence explanation that targets the misconception. Keep it concept-level "
    'and active. Respond ONLY as JSON: '
    '{"items": [{"question": string, "answer": string, "explanation": string}]}.'
)


def practice_items(
    title: str, body: str, misconception: str | None, subject: str | None = None
) -> list[dict]:
    """Generate a few retrieval-practice items targeting the question's misconception."""
    focus = misconception or title
    user = (
        f"Subject: {subject or 'this course'}.\n"
        f"Student's question: {title}\nDetails: {body or '(none)'}\n"
        f"Target misconception to remediate: {focus}"
    )
    try:
        resp = get_llm_provider().complete(
            [LLMMessage("system", _PRACTICE_SYSTEM), LLMMessage("user", user)], json_mode=True
        )
        data = extract_json(resp.text) or {}
        items = data.get("items") if isinstance(data, dict) else None
    except Exception as e:  # noqa: BLE001
        logger.warning("Sage practice generation failed: %s", e)
        items = None

    clean: list[dict] = []
    for it in items or []:
        if isinstance(it, dict) and it.get("question"):
            clean.append({
                "question": str(it.get("question")).strip(),
                "answer": str(it.get("answer") or "").strip(),
                "explanation": str(it.get("explanation") or "").strip(),
            })
    if clean:
        return clean[:5]
    # Deterministic fallback so the feature always works (e.g. with the mock provider).
    return [{
        "question": f"In your own words, explain the key idea behind: {focus}.",
        "answer": "Compare your explanation with your notes and the endorsed answer.",
        "explanation": "Retrieving and restating the concept yourself strengthens understanding.",
    }, {
        "question": f"Give one example where '{focus}' applies, and one where it does not.",
        "answer": "Any correct contrasting pair.",
        "explanation": "Contrasting cases expose the boundary of the concept and fix errors.",
    }]
