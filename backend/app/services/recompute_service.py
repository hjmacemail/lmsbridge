"""Recompute concept mastery (and re-trigger remediation) from the assessments
currently enabled for adaptive learning.

This makes the per-assessment `adaptive_enabled` toggle retroactive: after an admin
enables/disables assessments, recompute replays only the enabled results — in
chronological order, so the EWMA estimate is deterministic — then generates fresh
remediation for any concept that is now at-risk and has no open module.
"""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.models.assessment import Assessment, AssessmentResult
from app.models.concept import Concept
from app.models.course import Course
from app.models.enums import MasteryStatus, PedagogyStrategy
from app.models.mastery import ConceptMastery
from app.services import mastery_service
from app.services.ingestion_service import _has_open_module
from app.services.remediation_engine import generate_module

logger = get_logger("recompute")


def _latest_wrong_answer_result(db: Session, student_id: int, concept_key: str):
    """Most recent enabled result where this student got an MCQ wrong on the concept."""
    results = db.scalars(
        select(AssessmentResult)
        .join(Assessment, Assessment.id == AssessmentResult.assessment_id)
        .where(
            AssessmentResult.student_id == student_id,
            Assessment.adaptive_enabled.is_(True),
        )
        .order_by(AssessmentResult.ingested_at.desc())
    ).all()
    for r in results:
        for it in (r.item_scores or []):
            if it.get("concept_key") == concept_key and it.get("is_correct") is False:
                return r
    return None


def recompute_course(db: Session, course_id: int, auto_remediate: bool = True) -> dict:
    course = db.get(Course, course_id)
    if course is None:
        raise ValueError("Course not found")

    concepts = {c.key: c for c in db.scalars(
        select(Concept).where(Concept.course_id == course_id)
    ).all()}
    concept_ids = [c.id for c in concepts.values()]

    # Reset mastery for this course's concepts so the replay starts clean.
    if concept_ids:
        db.execute(delete(ConceptMastery).where(ConceptMastery.concept_id.in_(concept_ids)))
        db.flush()

    # Replay only enabled assessments, oldest first.
    results = db.scalars(
        select(AssessmentResult)
        .join(Assessment, Assessment.id == AssessmentResult.assessment_id)
        .where(Assessment.course_id == course_id, Assessment.adaptive_enabled.is_(True))
        .order_by(AssessmentResult.ingested_at, AssessmentResult.id)
    ).all()
    for r in results:
        for key, cscore in mastery_service.concept_scores_from_result(r).items():
            concept = concepts.get(key)
            if concept is not None:
                mastery_service.update_mastery(
                    db, student_id=r.student_id, concept_id=concept.id, observed_score=cscore
                )
    db.flush()

    # Trigger remediation for concepts now at-risk without an open module.
    triggered = 0
    if auto_remediate and concept_ids:
        at_risk = db.scalars(
            select(ConceptMastery)
            .where(
                ConceptMastery.concept_id.in_(concept_ids),
                ConceptMastery.status == MasteryStatus.at_risk,
            )
            .options(selectinload(ConceptMastery.concept))
        ).all()
        for m in at_risk:
            if _has_open_module(db, m.student_id, m.concept_id):
                continue
            generate_module(
                db,
                student_id=m.student_id,
                course_id=course_id,
                concept=m.concept,
                course_title=course.title,
                mastery_score=m.mastery_score,
                strategy=PedagogyStrategy.socratic_scaffolding,
                trigger_result=_latest_wrong_answer_result(db, m.student_id, m.concept.key),
            )
            triggered += 1

    db.commit()
    enabled = db.scalar(
        select(Assessment).where(
            Assessment.course_id == course_id, Assessment.adaptive_enabled.is_(True)
        )
    )
    summary = {
        "results_replayed": len(results),
        "modules_triggered": triggered,
        "has_enabled_assessments": enabled is not None,
    }
    logger.info("Recompute for course %s: %s", course_id, summary)
    return summary
