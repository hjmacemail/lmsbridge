"""Reset the seeded demo data back to a pristine state.

The public demo shares one seeded student/instructor, so anyone completing a tutor session
mutates that account (mastery bumps, completed modules, transcripts). This restores the
deterministic starting point: delete every remediation module (cascades to its activities,
tutor messages, and responses) and replay the original ingested results so mastery and the
open remediation modules are regenerated exactly as seeded.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.course import Course
from app.models.remediation import RemediationModule
from app.services.recompute_service import recompute_course

logger = get_logger("demo")


def reset_demo_data(db: Session) -> dict:
    courses = db.scalars(select(Course)).all()
    regenerated = 0
    for c in courses:
        # ORM delete so cascades remove activities, tutor messages, and responses.
        for m in db.scalars(
            select(RemediationModule).where(RemediationModule.course_id == c.id)
        ).all():
            db.delete(m)
        db.flush()
        regenerated += recompute_course(db, c.id).get("modules_triggered", 0)
    db.commit()
    summary = {"courses_reset": len(courses), "modules_regenerated": regenerated}
    logger.info("Demo reset: %s", summary)
    return summary
