from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_instructor
from app.db.session import get_db
from app.integrations.brightspace.factory import get_brightspace_adapter
from app.models.assessment import Assessment
from app.models.course import Course
from app.models.user import User
from app.schemas.assessment import AdaptiveToggle, AssessmentOut, ResultIngest, ResultOut
from app.services.ingestion_service import ingest_result
from app.services.recompute_service import recompute_course
from app.services.sync_service import sync_course_results

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("", response_model=list[AssessmentOut])
def list_assessments(
    course_id: int, db: Session = Depends(get_db), _: User = Depends(require_instructor)
) -> list[Assessment]:
    return list(
        db.scalars(
            select(Assessment)
            .where(Assessment.course_id == course_id)
            .order_by(Assessment.available_at)
        ).all()
    )


@router.patch("/{assessment_id}/adaptive", response_model=AssessmentOut)
def set_adaptive(
    assessment_id: int,
    payload: AdaptiveToggle,
    db: Session = Depends(get_db),
    _: User = Depends(require_instructor),
) -> Assessment:
    """Enable/disable whether this assessment's feedback drives adaptive learning."""
    assessment = db.get(Assessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    assessment.adaptive_enabled = payload.enabled
    db.commit()
    db.refresh(assessment)
    return assessment


@router.post("/recompute")
def recompute(
    course_id: int, db: Session = Depends(get_db), _: User = Depends(require_instructor)
) -> dict:
    """Rebuild mastery + remediation using only assessments enabled for adaptive learning."""
    if not db.get(Course, course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    return recompute_course(db, course_id)


@router.post("/results", response_model=ResultOut, status_code=201)
def ingest_single_result(
    payload: ResultIngest,
    db: Session = Depends(get_db),
    _: User = Depends(require_instructor),
) -> ResultOut:
    """Manually ingest one result (e.g. CSV import path) and trigger remediation."""
    assessment = db.get(Assessment, payload.assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    student = db.scalar(select(User).where(User.external_id == payload.student_external_id))
    if not student:
        raise HTTPException(status_code=404, detail="Student not found by external_id")
    result, _modules = ingest_result(
        db,
        assessment=assessment,
        student=student,
        score=payload.score,
        item_scores=[i.model_dump() for i in payload.item_scores],
        rubric_feedback=payload.rubric_feedback,
    )
    return result


@router.post("/sync")
def sync_from_brightspace(
    course_id: int, db: Session = Depends(get_db), _: User = Depends(require_instructor)
) -> dict:
    """Pull the latest results for a course from Brightspace and run remediation."""
    course = db.get(Course, course_id)
    if not course or not course.brightspace_course_id:
        raise HTTPException(status_code=400, detail="Course missing brightspace_course_id")
    return sync_course_results(
        db, course_id=course.id, course_external_id=course.brightspace_course_id,
        adapter=get_brightspace_adapter(),
    )
