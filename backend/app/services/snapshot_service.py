"""Record and read daily class-mastery snapshots so the dashboard can show real trends.

A snapshot is one row per (course, concept, day) holding that day's class-average mastery. We
upsert once per day (idempotent), so trends emerge naturally as the term progresses — and we never
fabricate movement: the trend is null until there is a prior day to compare against.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.concept import Concept
from app.models.enums import MasteryStatus
from app.models.mastery import ConceptMastery, MasterySnapshot


def record_snapshot(db: Session, course_id: int, on: date | None = None) -> None:
    """Upsert today's per-concept class-average mastery for a course."""
    day = on or date.today()
    concepts = db.scalars(select(Concept).where(Concept.course_id == course_id)).all()
    for c in concepts:
        rows = db.scalars(select(ConceptMastery).where(ConceptMastery.concept_id == c.id)).all()
        if not rows:
            continue
        avg = sum(r.mastery_score for r in rows) / len(rows)
        at_risk = sum(1 for r in rows if r.status == MasteryStatus.at_risk)
        existing = db.scalar(
            select(MasterySnapshot).where(
                MasterySnapshot.course_id == course_id,
                MasterySnapshot.concept_id == c.id,
                MasterySnapshot.taken_on == day,
            )
        )
        if existing:
            existing.avg_mastery = round(avg, 4)
            existing.at_risk_count = at_risk
        else:
            db.add(MasterySnapshot(
                course_id=course_id, concept_id=c.id,
                avg_mastery=round(avg, 4), at_risk_count=at_risk, taken_on=day,
            ))


def health_trend_pct(db: Session, course_id: int, current_health_pct: int | None) -> int | None:
    """Change in class health (percentage points) vs the most recent *prior* day on record.
    Returns None when there is no earlier snapshot to compare against (so no fake trend is shown)."""
    if current_health_pct is None:
        return None
    # Average mastery per day (mean over concepts), most recent days first.
    rows = db.execute(
        select(MasterySnapshot.taken_on, func.avg(MasterySnapshot.avg_mastery))
        .where(MasterySnapshot.course_id == course_id)
        .group_by(MasterySnapshot.taken_on)
        .order_by(MasterySnapshot.taken_on.desc())
    ).all()
    today = date.today()
    for taken_on, avg in rows:
        if taken_on < today:
            return current_health_pct - round(float(avg) * 100)
    return None
