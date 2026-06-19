"""Concept-mastery estimation from assessment evidence."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.assessment import AssessmentResult
from app.models.concept import Concept
from app.models.enums import MasteryStatus
from app.models.mastery import ConceptMastery


def _status_for(score: float) -> MasteryStatus:
    if score >= settings.mastery_threshold:
        return MasteryStatus.mastered
    if score <= settings.remediation_trigger_threshold:
        return MasteryStatus.at_risk
    return MasteryStatus.developing


def update_mastery(
    db: Session, *, student_id: int, concept_id: int, observed_score: float
) -> ConceptMastery:
    """Exponentially-weighted update of a student's mastery estimate for a concept.

    A simple, transparent estimator (EWMA) keeps the signal explainable to
    instructors. Newer evidence is weighted more heavily as evidence accumulates.
    """
    observed_score = max(0.0, min(1.0, observed_score))
    mastery = db.scalar(
        select(ConceptMastery).where(
            ConceptMastery.student_id == student_id,
            ConceptMastery.concept_id == concept_id,
        )
    )
    if mastery is None:
        mastery = ConceptMastery(
            student_id=student_id, concept_id=concept_id,
            mastery_score=observed_score, evidence_count=1,
        )
        db.add(mastery)
    else:
        alpha = 0.5  # weight on the newest observation
        mastery.mastery_score = round(
            alpha * observed_score + (1 - alpha) * mastery.mastery_score, 4
        )
        mastery.evidence_count += 1

    mastery.status = _status_for(mastery.mastery_score)
    mastery.last_evaluated_at = datetime.now(timezone.utc)
    db.flush()
    return mastery


def concept_scores_from_result(result: AssessmentResult) -> dict[str, float]:
    """Aggregate per-item AND rubric-criterion scores into normalized 0..1 per concept.

    Quizzes/exams carry per-question `item_scores`; assignments carry rubric criteria.
    Both are tagged with a `concept_key`, so we pool every available signal per concept.
    """
    totals: dict[str, list[float]] = {}
    for item in result.item_scores or []:
        key = item.get("concept_key")
        mx = item.get("max") or 0
        if key and mx > 0:
            totals.setdefault(key, []).append((item.get("earned", 0)) / mx)
    for crit in result.rubric_criteria or []:
        key = crit.get("concept_key")
        mx = crit.get("max_points") or 0
        if key and mx > 0:
            totals.setdefault(key, []).append((crit.get("points", 0)) / mx)
    return {k: sum(v) / len(v) for k, v in totals.items() if v}


def resolve_concepts(db: Session, course_id: int, keys: list[str]) -> dict[str, Concept]:
    rows = db.scalars(
        select(Concept).where(Concept.course_id == course_id, Concept.key.in_(keys))
    ).all()
    return {c.key: c for c in rows}
