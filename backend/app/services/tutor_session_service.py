"""Run the interactive AI-tutor session for a remediation module.

The student works through a live, turn-by-turn Socratic dialogue grounded in their own
wrong answers and the instructor's course material. The tutor decides when the session's
learning checkpoints are met; completing a session raises the student's concept mastery.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.llm.base import LLMMessage
from app.llm.providers.mock import extract_json
from app.llm.tenant_factory import resolve_provider
from app.models.assessment import AssessmentResult
from app.models.course import Course
from app.models.enums import RemediationStatus
from app.models.mastery import ConceptMastery
from app.models.remediation import RemediationModule, TutorMessage
from app.pedagogy.prompts import (
    build_tutor_opening_user_prompt,
    build_tutor_session_system_prompt,
)
from app.services import mastery_service
from app.services.remediation_engine import _evidence_summary

logger = get_logger("tutor")

# Mastery credit awarded when a student completes a tutoring session for a concept.
COMPLETION_MASTERY_SCORE = 0.85
# After this many student turns, the tutor wraps up gracefully so sessions never run forever.
MAX_STUDENT_TURNS = 10


def _clean_choices(data: dict) -> list[str] | None:
    """A tutor turn may include a short multiple-choice check. Keep 2–4 non-empty options."""
    raw = data.get("choices")
    if not isinstance(raw, list):
        return None
    opts = [str(c).strip() for c in raw if str(c).strip()]
    return opts[:4] if len(opts) >= 2 else None


def _has_wrong_mcq(result: AssessmentResult | None, concept_key: str) -> bool:
    if result is None:
        return False
    return any(
        it.get("concept_key") == concept_key and it.get("is_correct") is False
        for it in (result.item_scores or [])
    )


def _latest_wrong_answer_result(db: Session, student_id: int, concept_key: str):
    """Most recent result where the student got an MCQ on this concept wrong."""
    results = db.scalars(
        select(AssessmentResult)
        .where(AssessmentResult.student_id == student_id)
        .order_by(AssessmentResult.ingested_at.desc(), AssessmentResult.id.desc())
    ).all()
    for r in results:
        if _has_wrong_mcq(r, concept_key):
            return r
    return None


def _system_prompt(db: Session, module: RemediationModule, language: str | None = None) -> str:
    concept = module.concept
    course = db.get(Course, module.course_id)
    objectives = [a.prompt for a in module.activities]
    trigger = (
        db.get(AssessmentResult, module.trigger_result_id)
        if module.trigger_result_id else None
    )
    # Prefer evidence that includes an actual wrong multiple-choice answer for this concept,
    # so the tutor's questions are concrete and course-specific. The trigger may have been a
    # rubric-graded assignment (no per-question detail) — in that case look up the latest
    # result where the student got an MCQ on this concept wrong.
    if not _has_wrong_mcq(trigger, concept.key):
        better = _latest_wrong_answer_result(db, module.student_id, concept.key)
        trigger = better or trigger
    mastery = db.scalar(
        select(ConceptMastery).where(
            ConceptMastery.student_id == module.student_id,
            ConceptMastery.concept_id == module.concept_id,
        )
    )
    score = mastery.mastery_score if mastery else 0.5
    from app.services.material_service import grounding_excerpts
    excerpts = grounding_excerpts(db, course_id=module.course_id, concept=concept)
    return build_tutor_session_system_prompt(
        course_title=course.title if course else "",
        concept_name=concept.name,
        concept_description=concept.description,
        strategy=module.strategy,
        objectives=objectives,
        evidence_summary=_evidence_summary(concept, trigger, score),
        material_excerpts=excerpts,
        language=language,
    )


def session_context(db: Session, module: RemediationModule) -> dict:
    """Structured learning context for the tutoring UI: goal, plan, mastery, and the specific
    wrong answer that triggered the session. Everything here is already known server-side; this
    just surfaces it so the screen can show a real misconception card instead of only free text."""
    concept = module.concept
    objectives = [a.prompt for a in module.activities]
    mastery = db.scalar(
        select(ConceptMastery).where(
            ConceptMastery.student_id == module.student_id,
            ConceptMastery.concept_id == module.concept_id,
        )
    )
    trigger = (
        db.get(AssessmentResult, module.trigger_result_id)
        if module.trigger_result_id else None
    )
    if not _has_wrong_mcq(trigger, concept.key):
        trigger = _latest_wrong_answer_result(db, module.student_id, concept.key) or trigger
    evidence = None
    focus = None
    if trigger:
        for it in trigger.item_scores or []:
            if it.get("concept_key") == concept.key and it.get("is_correct") is False:
                evidence = {
                    "question": it.get("question"),
                    "chosen": it.get("selected"),
                    "correct": it.get("correct"),
                    "misconception": it.get("misconception"),
                }
                focus = it.get("misconception")
                break
    return {
        "concept_name": concept.name,
        "goal": concept.description,
        "objectives": objectives,
        "mastery_score": mastery.mastery_score if mastery else None,
        "focus_misconception": focus,
        "evidence": evidence,
    }


def _history(module: RemediationModule) -> list[LLMMessage]:
    out: list[LLMMessage] = []
    for m in module.messages:
        out.append(LLMMessage("assistant" if m.role == "tutor" else "user", m.content))
    return out


def _add(db: Session, module: RemediationModule, role: str, content: str,
         choices: list[str] | None = None) -> TutorMessage:
    seq = len(module.messages)
    msg = TutorMessage(
        module_id=module.id, sequence=seq, role=role, content=content,
        choices=json.dumps(choices) if choices else None,
    )
    db.add(msg)
    db.flush()
    module.messages.append(msg)
    return msg


def start_session(
    db: Session, module: RemediationModule, language: str | None = None
) -> RemediationModule:
    """Ensure the session has an opening tutor turn; mark the module in-progress."""
    if module.messages:
        return module
    llm = resolve_provider(db, course_id=module.course_id)
    resp = llm.complete(
        [
            LLMMessage("system", _system_prompt(db, module, language)),
            LLMMessage("user", build_tutor_opening_user_prompt()),
        ],
        json_mode=True,
    )
    choices = None
    try:
        data = extract_json(resp.text)
        reply = data.get("reply") or _fallback_opening(module)
        choices = _clean_choices(data)
    except Exception:  # noqa: BLE001
        reply = _fallback_opening(module)
    _add(db, module, "tutor", reply, choices)
    if module.status == RemediationStatus.pending:
        module.status = RemediationStatus.in_progress
    db.commit()
    db.refresh(module)
    return module


def post_message(
    db: Session, module: RemediationModule, student_text: str, language: str | None = None
) -> dict:
    """Append the student's message, get the tutor's reply, and detect completion."""
    _add(db, module, "student", student_text)

    student_turns = sum(1 for m in module.messages if m.role == "student")
    at_limit = student_turns >= MAX_STUDENT_TURNS

    llm = resolve_provider(db, course_id=module.course_id)
    messages = [LLMMessage("system", _system_prompt(db, module, language)), *_history(module)]
    if at_limit:
        messages.append(LLMMessage("system",
            "SESSION LIMIT REACHED: this must be the FINAL turn. Give a brief, encouraging "
            "wrap-up that summarizes the key idea. Do NOT ask another question or include "
            "choices. Set \"complete\": true."))
    resp = llm.complete(messages, json_mode=True)
    choices = None
    try:
        data = extract_json(resp.text)
        reply = data.get("reply") or "Keep going — tell me more about your reasoning."
        complete = bool(data.get("complete"))
        choices = None if at_limit else _clean_choices(data)
    except Exception:  # noqa: BLE001
        reply, complete = "Keep going — walk me through your reasoning step by step.", False

    if at_limit:
        complete = True  # enforce the cap even if the model doesn't comply

    _add(db, module, "tutor", reply, choices)

    if complete:
        module.status = RemediationStatus.completed
        module.completed_at = datetime.now(timezone.utc)
        # Completing the session is evidence of improvement -> raise mastery.
        mastery_service.update_mastery(
            db, student_id=module.student_id, concept_id=module.concept_id,
            observed_score=COMPLETION_MASTERY_SCORE,
        )
        logger.info(
            "Tutor session for module #%s completed; mastery for concept %s raised.",
            module.id, module.concept_id,
        )

    db.commit()
    db.refresh(module)
    return {"reply": reply, "complete": complete, "status": module.status.value,
            "choices": choices}


def _fallback_opening(module: RemediationModule) -> str:
    return (
        f"Hi! Let's work through {module.concept.name} together. To start, tell me in your own "
        "words what you understand so far — and where you think it got tricky."
    )
