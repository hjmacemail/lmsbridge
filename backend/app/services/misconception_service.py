"""Misconception clusters: group students by the *specific* wrong idea they share on a concept.

Turns rows of individual wrong answers into "6 students confuse carry with overflow" — so an
instructor can teach the group, not chase individuals. Built entirely from real assessment
item-level evidence (the chosen distractor reveals the misconception); nothing is invented.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentResult
from app.models.concept import Concept
from app.models.course import Enrollment
from app.models.enums import UserRole
from app.models.user import User


def build_misconception_clusters(db: Session, course_id: int, limit: int = 12) -> list[dict]:
    concept_names = {
        c.key: c.name
        for c in db.scalars(select(Concept).where(Concept.course_id == course_id)).all()
    }
    if not concept_names:
        return []

    student_ids = [
        r for r in db.scalars(
            select(Enrollment.user_id).where(
                Enrollment.course_id == course_id, Enrollment.role == UserRole.student
            )
        ).all()
    ]
    if not student_ids:
        return []
    names = {
        u.id: u.full_name
        for u in db.scalars(select(User).where(User.id.in_(student_ids))).all()
    }

    # (concept_key, misconception) -> set(student_id)
    clusters: dict[tuple[str, str], set[int]] = {}
    results = db.scalars(
        select(AssessmentResult).where(AssessmentResult.student_id.in_(student_ids))
    ).all()
    for r in results:
        for it in (r.item_scores or []):
            if it.get("is_correct") is False and it.get("concept_key") in concept_names:
                misc = (it.get("misconception") or "").strip()
                if not misc:
                    continue
                clusters.setdefault((it["concept_key"], misc), set()).add(r.student_id)

    out = [
        {
            "concept": concept_names.get(ck, ck),
            "misconception": misc,
            "students": sorted(names.get(s, f"Student {s}") for s in sids),
            "size": len(sids),
        }
        for (ck, misc), sids in clusters.items()
    ]
    out.sort(key=lambda c: c["size"], reverse=True)
    return out[:limit]
