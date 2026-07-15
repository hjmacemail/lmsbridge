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


def build_class_brief(db: Session, course_id: int, lang: str | None = None) -> dict:
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

    brief, recommendation = _narrate(db, course_id, facts, lang)

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


def _narrate(db: Session, course_id: int, facts: dict, lang: str | None = None) -> tuple[str, str]:
    """Ask the model to narrate the real numbers; fall back to a template if it can't."""
    try:
        system, user = build_class_brief_prompt(facts, lang)
        llm = resolve_provider(db, course_id=course_id)
        resp = llm.complete([LLMMessage("system", system), LLMMessage("user", user)], json_mode=True)
        data = extract_json(resp.text)
        brief = (data.get("brief") or "").strip()
        rec = (data.get("recommendation") or "").strip()
        if brief and rec:
            return brief, rec
    except Exception as e:  # noqa: BLE001
        logger.info("Class-brief narration fell back to template: %s", e)
    return _template(facts, lang)


# Localized templates for the offline/mock fallback (the LLM path localizes on its own).
# {h}=class health %, {n}=needing attention, {tot}=total students, {gap}=biggest-gap concept,
# {gm}=gap mastery %, {sess}=tutoring sessions, {done}=sessions completed, {at}=students at risk.
_TEMPLATES = {
    "en": {
        "empty": ("No mastery data yet — run a sync or wait for the first assessments to come in.",
                  "Import an assessment or connect your LMS to start seeing class insights."),
        "brief": ("Class mastery is around {h}% across the tracked concepts. {n} of {tot} students "
                  "need attention, and {gap} is the biggest gap at {gm}%. The AI tutor has run "
                  "{sess} sessions ({done} completed)."),
        "rec": ("Spend ~10 minutes reviewing {gap} before your next lecture — it's the "
                "highest-impact fix, affecting {at} students."),
    },
    "es": {
        "empty": ("Aún no hay datos de dominio — ejecuta una sincronización o espera a las primeras evaluaciones.",
                  "Importa una evaluación o conecta tu LMS para empezar a ver información de la clase."),
        "brief": ("El dominio de la clase ronda el {h}% en los conceptos seguidos. {n} de {tot} "
                  "estudiantes necesitan atención, y {gap} es la mayor brecha con un {gm}%. El tutor "
                  "de IA ha realizado {sess} sesiones ({done} completadas)."),
        "rec": ("Dedica ~10 minutos a repasar {gap} antes de tu próxima clase — es la mejora de mayor "
                "impacto, afecta a {at} estudiantes."),
    },
    "fr": {
        "empty": ("Pas encore de données de maîtrise — lancez une synchronisation ou attendez les premières évaluations.",
                  "Importez une évaluation ou connectez votre LMS pour commencer à voir les informations de la classe."),
        "brief": ("La maîtrise de la classe est d'environ {h}% sur les concepts suivis. {n} étudiants "
                  "sur {tot} ont besoin d'attention, et {gap} est le plus grand écart à {gm}%. Le tuteur "
                  "IA a mené {sess} sessions ({done} terminées)."),
        "rec": ("Consacrez ~10 minutes à revoir {gap} avant votre prochain cours — c'est la correction "
                "la plus utile, elle concerne {at} étudiants."),
    },
    "ar": {
        "empty": ("لا توجد بيانات إتقان بعد — شغّل مزامنة أو انتظر وصول أول التقييمات.",
                  "استورد تقييمًا أو اربط نظامك التعليمي لتبدأ برؤية معلومات الصف."),
        "brief": ("يبلغ إتقان الصف نحو {h}% عبر المفاهيم المتابَعة. {n} من {tot} طالبًا يحتاجون إلى "
                  "انتباه، و{gap} هو أكبر فجوة عند {gm}%. أجرى مُعلّم الذكاء الاصطناعي {sess} جلسة "
                  "({done} مكتملة)."),
        "rec": ("خصّص نحو 10 دقائق لمراجعة {gap} قبل حصّتك القادمة — فهي الأعلى أثرًا، وتخصّ {at} طالبًا."),
    },
}


def _template(f: dict, lang: str | None = None) -> tuple[str, str]:
    tpl = _TEMPLATES.get((lang or "en")[:2], _TEMPLATES["en"])
    if not f["biggest_gap_concept"]:
        return tpl["empty"]
    vals = dict(
        h=f["class_health_pct"], n=f["students_needing_attention"], tot=f["students_total"],
        gap=f["biggest_gap_concept"], gm=f["biggest_gap_mastery_pct"],
        sess=f["ai_tutoring_sessions"], done=f["ai_sessions_completed"],
        at=f["biggest_gap_students_at_risk"],
    )
    return tpl["brief"].format(**vals), tpl["rec"].format(**vals)
