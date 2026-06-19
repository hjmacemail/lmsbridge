"""Sync Brightspace analytics into LMS Bridge and run the remediation pipeline.

Idempotent-ish: matches courses/students/assessments by their external ids.
In production this would run on a schedule (e.g. a Celery beat / cron poll).
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.integrations.brightspace.base import BrightspaceAdapter
from app.integrations.brightspace.factory import get_brightspace_adapter
from app.models.assessment import Assessment
from app.models.course import Enrollment
from app.models.enums import AssessmentType, UserRole
from app.models.user import User
from app.services.ingestion_service import ingest_result

logger = get_logger("sync")


def _ensure_enrollment(db: Session, user_id: int, course_id: int) -> None:
    exists = db.scalar(
        select(Enrollment).where(
            Enrollment.user_id == user_id, Enrollment.course_id == course_id
        )
    )
    if not exists:
        db.add(Enrollment(user_id=user_id, course_id=course_id, role=UserRole.student))
        db.flush()


def _get_or_create_student(db: Session, ext_id: str, name: str, email: str) -> User:
    user = db.scalar(select(User).where(User.external_id == ext_id))
    if user:
        return user
    user = db.scalar(select(User).where(User.email == email))
    if user:
        user.external_id = ext_id
        return user
    from app.core.security import hash_password
    user = User(
        email=email, full_name=name, external_id=ext_id,
        role=UserRole.student, hashed_password=hash_password("changeme123"),
    )
    db.add(user)
    db.flush()
    return user


def sync_course_results(
    db: Session, course_id: int, course_external_id: str,
    adapter: BrightspaceAdapter | None = None, auto_remediate: bool = True,
) -> dict:
    """Pull new results for a course and run them through the ingestion pipeline."""
    adapter = adapter or get_brightspace_adapter()
    results = adapter.fetch_new_results(course_external_id)
    ingested, modules = 0, 0
    for r in results:
        assessment = db.scalar(
            select(Assessment).where(
                Assessment.brightspace_assessment_id == r.assessment_external_id
            )
        )
        if assessment is None:
            try:
                atype = AssessmentType(r.assessment_type)
            except ValueError:
                atype = AssessmentType.quiz
            assessment = Assessment(
                course_id=course_id,
                brightspace_assessment_id=r.assessment_external_id,
                title=r.assessment_title or r.assessment_external_id,
                type=atype,
                max_score=r.assessment_max_score,
                available_at=r.available_at or datetime.now(timezone.utc),
            )
            db.add(assessment)
            db.flush()

        students = {s.external_id: s for s in adapter.list_students(course_external_id)}
        meta = students.get(r.student_external_id)
        student = _get_or_create_student(
            db, r.student_external_id,
            meta.full_name if meta else r.student_external_id,
            meta.email if meta else f"{r.student_external_id}@student.example.edu",
        )
        _ensure_enrollment(db, student.id, course_id)
        _, mods = ingest_result(
            db,
            assessment=assessment,
            student=student,
            score=r.score,
            item_scores=[i.__dict__ for i in r.item_scores],
            rubric_feedback=r.rubric_feedback,
            rubric_criteria=[c.__dict__ for c in r.rubric_criteria],
            attempts=r.attempts,
            time_on_task_minutes=r.time_on_task_minutes,
            submitted_late=r.submitted_late,
            auto_remediate=auto_remediate,
        )
        ingested += 1
        modules += len(mods)

    summary = {"adapter": adapter.name, "results_ingested": ingested, "modules_triggered": modules}
    logger.info("Sync complete: %s", summary)
    return summary
