"""AI Classroom Brief ("Instructor Copilot").

Answers the one question an instructor actually has — *what should I do before my next class?* —
by computing the class's real numbers (mastery, at-risk students, the biggest concept gap, AI
activity) and asking the model ONLY to narrate them. The figures are always real; the model adds
the human summary and a concrete recommendation. If the model is unavailable, a templated brief is
returned from the same real numbers, so this never fabricates data.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.llm.base import LLMMessage
from app.llm.providers.mock import extract_json
from app.llm.tenant_factory import resolve_provider
from app.models.concept import Concept
from app.models.course import Course, Enrollment
from app.models.enums import MasteryStatus, RemediationStatus, UserRole
from app.models.mastery import ConceptMastery
from app.models.remediation import RemediationModule
from app.pedagogy.prompts import build_class_brief_prompt

logger = get_logger("brief")


def build_class_brief(db: Session, course_id: int) -> dict:
    course = db.get(Course, course_id)
    concepts = db.scalars(
        select(Concept).where(Concept.course_id == course_id).order_by(Concept.sequence)
    ).all()

    risks = []
    for c in concepts:
        rows = db.scalars(select(ConceptMastery).where(ConceptMastery.concept_id == c.id)).all()
        if not rows:
            continue
        avg = sum(r.mastery_score for r in rows) / len(rows)
        at_risk = sum(1 for r in rows if r.status == MasteryStatus.at_risk)
        risks.append({"concept": c, "avg": avg, "at_risk": at_risk, "total": len(rows)})
    risks.sort(key=lambda r: r["avg"])

    health = round(sum(r["avg"] for r in risks) / len(risks) * 100) if risks else None
    students_total = db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.course_id == course_id, Enrollment.role == UserRole.student
        )
    ) or 0

    concept_ids = [c.id for c in concepts]
    needs_attention = 0
    if concept_ids:
        needs_attention = len(db.execute(
            select(ConceptMastery.student_id)
            .where(ConceptMastery.concept_id.in_(concept_ids),
                   ConceptMastery.status == MasteryStatus.at_risk)
            .distinct()
        ).all())

    ai_sessions = db.scalar(
        select(func.count(RemediationModule.id)).where(RemediationModule.course_id == course_id)
    ) or 0
    ai_completed = db.scalar(
        select(func.count(RemediationModule.id)).where(
            RemediationModule.course_id == course_id,
            RemediationModule.status == RemediationStatus.completed,
        )
    ) or 0
    not_started = db.scalar(
        select(func.count(RemediationModule.id)).where(
            RemediationModule.course_id == course_id,
            RemediationModule.status == RemediationStatus.pending,
        )
    ) or 0

    top = risks[0] if risks else None
    top_name = top["concept"].name if top else None
    top_mastery = round(top["avg"] * 100) if top else None
    top_affected = top["at_risk"] if top else None
    top_misc = None
    if top and top["concept"].common_misconceptions:
        top_misc = top["concept"].common_misconceptions.strip().splitlines()[0].strip()

    facts = {
        "course": course.title if course else "",
        "class_health_pct": health,
        "students_total": students_total,
        "students_needing_attention": needs_attention,
        "biggest_gap_concept": top_name,
        "biggest_gap_mastery_pct": top_mastery,
        "biggest_gap_students_at_risk": top_affected,
        "likely_misconception": top_misc,
        "ai_tutoring_sessions": ai_sessions,
        "ai_sessions_completed": ai_completed,
        "remediation_not_started": not_started,
    }

    from app.services.snapshot_service import health_trend_pct
    trend = health_trend_pct(db, course_id, health)
    facts["class_health_change_pts"] = trend

    brief, recommendation = _narrate(db, course_id, facts)

    return {
        "health_pct": health,
        "health_trend": trend,
        "students_total": students_total,
        "needs_attention": needs_attention,
        "top_concept": top_name,
        "top_concept_mastery": top_mastery,
        "top_concept_affected": top_affected,
        "top_misconception": top_misc,
        "ai_sessions": ai_sessions,
        "ai_completed": ai_completed,
        "not_started": not_started,
        "brief": brief,
        "recommendation": recommendation,
    }


def _narrate(db: Session, course_id: int, facts: dict) -> tuple[str, str]:
    """Ask the model to narrate the real numbers; fall back to a template if it can't."""
    try:
        system, user = build_class_brief_prompt(facts)
        llm = resolve_provider(db, course_id=course_id)
        resp = llm.complete([LLMMessage("system", system), LLMMessage("user", user)], json_mode=True)
        data = extract_json(resp.text)
        brief = (data.get("brief") or "").strip()
        rec = (data.get("recommendation") or "").strip()
        if brief and rec:
            return brief, rec
    except Exception as e:  # noqa: BLE001
        logger.info("Class-brief narration fell back to template: %s", e)
    return _template(facts)


def _template(f: dict) -> tuple[str, str]:
    if not f["biggest_gap_concept"]:
        return ("No mastery data yet — run a sync or wait for the first assessments to come in.",
                "Import an assessment or connect your LMS to start seeing class insights.")
    brief = (
        f"Class mastery is around {f['class_health_pct']}% across the tracked concepts. "
        f"{f['students_needing_attention']} of {f['students_total']} students need attention, and "
        f"{f['biggest_gap_concept']} is the biggest gap at {f['biggest_gap_mastery_pct']}%"
        + (f" — likely because they {f['likely_misconception'][0].lower()}{f['likely_misconception'][1:]}"
           if f.get("likely_misconception") else "")
        + f". The AI tutor has run {f['ai_tutoring_sessions']} sessions "
        f"({f['ai_sessions_completed']} completed)."
    )
    rec = (
        f"Spend ~10 minutes reviewing {f['biggest_gap_concept']} before your next lecture — "
        f"it's the highest-impact fix, affecting {f['biggest_gap_students_at_risk']} students."
    )
    return brief, rec
