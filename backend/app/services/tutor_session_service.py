"""Run the interactive AI-tutor session for a remediation module.

The student works through a live, turn-by-turn Socratic dialogue grounded in their own
wrong answers and the instructor's course material. The tutor decides when the session's
learning checkpoints are met; completing a session raises the student's concept mastery.
"""
from __future__ import annotations

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


def _history(module: RemediationModule) -> list[LLMMessage]:
    out: list[LLMMessage] = []
    for m in module.messages:
        out.append(LLMMessage("assistant" if m.role == "tutor" else "user", m.content))
    return out


def _add(db: Session, module: RemediationModule, role: str, content: str) -> TutorMessage:
    seq = len(module.messages)
    msg = TutorMessage(module_id=module.id, sequence=seq, role=role, content=content)
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
    try:
        data = extract_json(resp.text)
        reply = data.get("reply") or _fallback_opening(module)
    except Exception:  # noqa: BLE001
        reply = _fallback_opening(module)
    _add(db, module, "tutor", reply)
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

    llm = resolve_provider(db, course_id=module.course_id)
    messages = [LLMMessage("system", _system_prompt(db, module, language)), *_history(module)]
    resp = llm.complete(messages, json_mode=True)
    try:
        data = extract_json(resp.text)
        reply = data.get("reply") or "Keep going — tell me more about your reasoning."
        complete = bool(data.get("complete"))
    except Exception:  # noqa: BLE001
        reply, complete = "Keep going — walk me through your reasoning step by step.", False

    _add(db, module, "tutor", reply)

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
    return {"reply": reply, "complete": complete, "status": module.status.value}


def _fallback_opening(module: RemediationModule) -> str:
    return (
        f"Hi! Let's work through {module.concept.name} together. To start, tell me in your own "
        "words what you understand so far — and where you think it got tricky."
    )
