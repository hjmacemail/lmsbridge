"""Reset the seeded demo data back to a pristine state.

The public demo shares one seeded student/instructor, so anyone completing a tutor session
mutates that account (mastery bumps, completed modules, transcripts). Reset restores the
deterministic starting point — and, importantly, it RE-PULLS from the (mock) LMS so the demo
reflects the current data generator (e.g. multiple "recommended to review" topics) even on a
database that was seeded by an older build. Only LMS-backed demo courses are touched; standalone
Sage courses (no `brightspace_course_id`) are left alone.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.assessment import Assessment, AssessmentResult
from app.models.concept import Concept
from app.models.course import Course
from app.models.mastery import ConceptMastery
from app.models.remediation import RemediationModule
from app.services.sync_service import sync_course_results

logger = get_logger("demo")


def reset_demo_data(db: Session) -> dict:
    courses = db.scalars(select(Course).where(Course.brightspace_course_id.is_not(None))).all()
    regenerated = 0
    for c in courses:
        # Clear remediation modules (cascades to activities/messages/responses), the ingested
        # assessment results, and concept mastery — so everything regenerates from the mock.
        for m in db.scalars(
            select(RemediationModule).where(RemediationModule.course_id == c.id)
        ).all():
            db.delete(m)
        assess_ids = list(db.scalars(
            select(Assessment.id).where(Assessment.course_id == c.id)).all())
        if assess_ids:
            for r in db.scalars(
                select(AssessmentResult).where(AssessmentResult.assessment_id.in_(assess_ids))
            ).all():
                db.delete(r)
        concept_ids = list(db.scalars(
            select(Concept.id).where(Concept.course_id == c.id)).all())
        if concept_ids:
            for cm in db.scalars(
                select(ConceptMastery).where(ConceptMastery.concept_id.in_(concept_ids))
            ).all():
                db.delete(cm)
        db.flush()
        # Re-pull from the (mock) LMS to regenerate results + mastery + remediation.
        summary = sync_course_results(db, c.id, c.brightspace_course_id)
        regenerated += summary.get("modules_triggered", 0)
    db.commit()
    out = {"courses_reset": len(courses), "modules_regenerated": regenerated}
    logger.info("Demo reset: %s", out)
    return out
