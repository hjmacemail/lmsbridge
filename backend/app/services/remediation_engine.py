"""The remediation engine: turns a flagged concept gap into a tailored module,
and evaluates student responses — all through the pedagogically-constrained LLM.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.llm.base import LLMMessage
from app.llm.providers.mock import extract_json
from app.llm.tenant_factory import resolve_provider
from app.models.assessment import AssessmentResult
from app.models.concept import Concept
from app.models.enums import ActivityType, PedagogyStrategy, RemediationStatus
from app.models.remediation import RemediationActivity, RemediationModule, StudentResponse
from app.pedagogy.prompts import (
    TUTOR_SYSTEM_PROMPT,
    build_feedback_prompt,
    build_generation_prompt,
)
from app.services import material_service

logger = get_logger("remediation")


def _evidence_summary(concept: Concept, result: AssessmentResult | None, score: float) -> str:
    lines = [f"Estimated mastery of '{concept.name}': {score:.0%}."]
    if result is None:
        return "\n".join(lines)

    lines.append(f"Triggered by assessment result #{result.id} (overall {result.score:.0%}).")

    # Multiple-choice answers are the strongest signal: the specific WRONG option a student
    # chose reveals a specific misconception. List the missed questions for this concept.
    missed = [
        it for it in (result.item_scores or [])
        if it.get("concept_key") == concept.key and it.get("is_correct") is False
    ]
    if missed:
        lines.append("Questions answered incorrectly on this concept (use these to target the "
                     "remediation — the chosen option reveals the misconception):")
        for it in missed:
            q = it.get("question", "")
            chosen = it.get("selected", "")
            correct = it.get("correct", "")
            misc = it.get("misconception")
            lines.append(f'- Q: "{q}"')
            lines.append(f'    chose "{chosen}" (correct: "{correct}")')
            if misc:
                lines.append(f"    -> likely misconception: {misc}")

    # Fall back to coarse per-item score for non-MCQ (rubric-only) evidence.
    if not missed:
        for item in result.item_scores or []:
            if item.get("concept_key") == concept.key and item.get("max"):
                pct = item["earned"] / item["max"]
                lines.append(f"- Item scored {pct:.0%} on this concept.")

    if result.rubric_feedback:
        lines.append(f"Rubric feedback: {result.rubric_feedback}")
    return "\n".join(lines)


def generate_module(
    db: Session,
    *,
    student_id: int,
    course_id: int,
    concept: Concept,
    course_title: str,
    mastery_score: float,
    strategy: PedagogyStrategy = PedagogyStrategy.socratic_scaffolding,
    trigger_result: AssessmentResult | None = None,
) -> RemediationModule:
    """Generate and persist a remediation module for one student + concept."""
    llm = resolve_provider(db, course_id=course_id)
    excerpts = material_service.grounding_excerpts(
        db, course_id=course_id, concept=concept
    )
    prompt = build_generation_prompt(
        course_title=course_title,
        concept_name=concept.name,
        concept_description=concept.description,
        common_misconceptions=concept.common_misconceptions,
        strategy=strategy,
        evidence_summary=_evidence_summary(concept, trigger_result, mastery_score),
        material_excerpts=excerpts,
    )
    resp = llm.complete(
        [LLMMessage("system", TUTOR_SYSTEM_PROMPT), LLMMessage("user", prompt)],
        json_mode=True,
    )
    try:
        data = extract_json(resp.text)
    except (ValueError, Exception) as e:  # noqa: BLE001
        logger.error("Failed to parse module JSON (%s); using safe fallback.", e)
        data = {}
    # Always guarantee at least one active activity, even if the model returns none.
    if not data.get("activities"):
        logger.warning("Model returned no activities for '%s'; using safe fallback.", concept.key)
        data.setdefault("title", f"Review: {concept.name}")
        data.setdefault("rationale", "Auto-generated review based on recent performance.")
        data["activities"] = [
            {"activity_type": "retrieval",
             "prompt": f"In your own words, explain {concept.name}.",
             "payload": {"focus": "recall"}},
        ]

    module = RemediationModule(
        student_id=student_id,
        course_id=course_id,
        concept_id=concept.id,
        trigger_result_id=trigger_result.id if trigger_result else None,
        strategy=strategy,
        status=RemediationStatus.pending,
        title=data.get("title", f"Review: {concept.name}")[:255],
        rationale=data.get("rationale"),
        generated_by_model=f"{resp.provider}:{resp.model}",
        grounded_on=[e["title"] for e in excerpts] or None,
    )
    db.add(module)
    db.flush()

    for i, act in enumerate(data.get("activities", [])):
        try:
            atype = ActivityType(act.get("activity_type", "socratic"))
        except ValueError:
            atype = ActivityType.socratic
        db.add(
            RemediationActivity(
                module_id=module.id,
                sequence=i,
                activity_type=atype,
                prompt=act.get("prompt", ""),
                payload=act.get("payload"),
            )
        )
    db.flush()
    db.refresh(module)
    logger.info(
        "Generated module #%s (%s activities) for student %s on concept '%s'",
        module.id, len(module.activities), student_id, concept.key,
    )
    return module


def evaluate_response(
    db: Session, *, activity: RemediationActivity, student_id: int, response_text: str
) -> StudentResponse:
    """Run the constrained tutor to give formative feedback on a student response."""
    llm = resolve_provider(db, course_id=activity.module.course_id)
    concept = activity.module.concept
    prompt = build_feedback_prompt(
        concept_name=concept.name,
        activity_prompt=activity.prompt,
        student_response=response_text,
    )
    resp = llm.complete(
        [LLMMessage("system", TUTOR_SYSTEM_PROMPT), LLMMessage("user", prompt)],
        json_mode=True,
    )
    try:
        data = extract_json(resp.text)
    except Exception:  # noqa: BLE001
        data = {"is_correct": None, "resolves_misconception": None,
                "feedback": "Thanks — keep going. Re-state the rule you're applying."}

    sr = StudentResponse(
        activity_id=activity.id,
        student_id=student_id,
        response_text=response_text,
        is_correct=data.get("is_correct"),
        feedback=data.get("feedback"),
        resolves_misconception=data.get("resolves_misconception"),
    )
    db.add(sr)
    db.flush()
    return sr
