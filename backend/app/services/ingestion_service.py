"""Ingestion pipeline: assessment result -> mastery update -> just-in-time remediation.

This is the heart of the 'just-in-time' behavior: when a formative assessment result
arrives, the system updates concept mastery and, for any concept that drops to
'at risk', automatically generates a tailored remediation module.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.assessment import Assessment, AssessmentResult
from app.models.enums import MasteryStatus, PedagogyStrategy, RemediationStatus
from app.models.remediation import RemediationModule
from app.models.user import User
from app.services import mastery_service
from app.services.remediation_engine import generate_module

logger = get_logger("ingestion")


def ingest_result(
    db: Session,
    *,
    assessment: Assessment,
    student: User,
    score: float,
    item_scores: list[dict],
    rubric_feedback: str | None = None,
    rubric_criteria: list[dict] | None = None,
    attempts: int | None = None,
    time_on_task_minutes: float | None = None,
    submitted_late: bool | None = None,
    auto_remediate: bool = True,
) -> tuple[AssessmentResult, list[RemediationModule]]:
    """Persist a result, update mastery, and trigger remediation for at-risk concepts."""
    result = AssessmentResult(
        assessment_id=assessment.id,
        student_id=student.id,
        score=max(0.0, min(1.0, score)),
        item_scores=item_scores,
        rubric_feedback=rubric_feedback,
        rubric_criteria=rubric_criteria,
        attempts=attempts,
        time_on_task_minutes=time_on_task_minutes,
        submitted_late=submitted_late,
        ingested_at=datetime.now(timezone.utc),
    )
    db.add(result)
    db.flush()

    # Record the result, but if the admin has disabled this assessment for adaptive
    # learning, do not let it influence mastery or trigger remediation.
    if not assessment.adaptive_enabled:
        db.commit()
        db.refresh(result)
        logger.info(
            "Recorded result for %s on '%s' (adaptive disabled — not used for remediation)",
            student.email, assessment.title,
        )
        return result, []

    per_concept = mastery_service.concept_scores_from_result(result)
    concepts = mastery_service.resolve_concepts(db, assessment.course_id, list(per_concept))

    triggered: list[RemediationModule] = []
    for key, cscore in per_concept.items():
        concept = concepts.get(key)
        if concept is None:
            logger.warning("Unknown concept key '%s' on course %s", key, assessment.course_id)
            continue
        mastery = mastery_service.update_mastery(
            db, student_id=student.id, concept_id=concept.id, observed_score=cscore
        )
        if (
            auto_remediate
            and mastery.status == MasteryStatus.at_risk
            and not _has_open_module(db, student.id, concept.id)
        ):
            module = generate_module(
                db,
                student_id=student.id,
                course_id=assessment.course_id,
                concept=concept,
                course_title=assessment.course.title,
                mastery_score=mastery.mastery_score,
                strategy=PedagogyStrategy.socratic_scaffolding,
                trigger_result=result,
            )
            triggered.append(module)

    db.commit()
    db.refresh(result)
    logger.info(
        "Ingested result for %s on '%s': %d concepts, %d remediation module(s) triggered",
        student.email, assessment.title, len(per_concept), len(triggered),
    )
    return result, triggered


def _has_open_module(db: Session, student_id: int, concept_id: int) -> bool:
    existing = db.scalar(
        select(RemediationModule).where(
            RemediationModule.student_id == student_id,
            RemediationModule.concept_id == concept_id,
            RemediationModule.status.in_(
                [RemediationStatus.pending, RemediationStatus.in_progress]
            ),
        )
    )
    return existing is not None
