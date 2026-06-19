from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.concept import Concept
from app.models.course import Course, Enrollment
from app.models.enums import RemediationStatus, UserRole
from app.models.mastery import ConceptMastery
from app.models.remediation import RemediationModule
from app.models.user import User
from app.schemas.course import CourseOut
from app.schemas.remediation import MasteryOut, StudentDashboard

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/me/courses", response_model=list[CourseOut])
def my_courses(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[Course]:
    """Courses the current user is enrolled in (for the student course picker)."""
    return list(
        db.scalars(
            select(Course)
            .join(Enrollment, Enrollment.course_id == Course.id)
            .where(Enrollment.user_id == user.id)
            .order_by(Course.code)
        ).all()
    )


@router.get("/me/dashboard", response_model=StudentDashboard)
def my_dashboard(
    course_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StudentDashboard:
    return _dashboard_for(db, user, course_id)


@router.get("/{student_id}/dashboard", response_model=StudentDashboard)
def student_dashboard(
    student_id: int,
    course_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StudentDashboard:
    if user.role == UserRole.student and user.id != student_id:
        raise HTTPException(status_code=403, detail="Students may only view their own dashboard")
    student = db.get(User, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return _dashboard_for(db, student, course_id)


def _dashboard_for(
    db: Session, student: User, course_id: int | None = None
) -> StudentDashboard:
    mastery_q = (
        select(ConceptMastery)
        .where(ConceptMastery.student_id == student.id)
        .options(selectinload(ConceptMastery.concept))
    )
    if course_id is not None:
        mastery_q = mastery_q.join(Concept, Concept.id == ConceptMastery.concept_id).where(
            Concept.course_id == course_id
        )
    masteries = [
        MasteryOut(
            concept_id=m.concept_id,
            concept_key=m.concept.key if m.concept else None,
            concept_name=m.concept.name if m.concept else None,
            mastery_score=m.mastery_score,
            status=m.status,
            evidence_count=m.evidence_count,
        )
        for m in db.scalars(mastery_q).all()
    ]

    modules_q = (
        select(RemediationModule)
        .where(
            RemediationModule.student_id == student.id,
            RemediationModule.status.in_(
                [RemediationStatus.pending, RemediationStatus.in_progress]
            ),
        )
        .options(selectinload(RemediationModule.activities))
        .order_by(RemediationModule.created_at.desc())
    )
    if course_id is not None:
        modules_q = modules_q.where(RemediationModule.course_id == course_id)
    open_modules = list(db.scalars(modules_q).all())

    completed_q = select(func.count(RemediationModule.id)).where(
        RemediationModule.student_id == student.id,
        RemediationModule.status == RemediationStatus.completed,
    )
    if course_id is not None:
        completed_q = completed_q.where(RemediationModule.course_id == course_id)
    completed_count = db.scalar(completed_q) or 0

    return StudentDashboard(
        student_id=student.id,
        full_name=student.full_name,
        masteries=masteries,
        open_modules=open_modules,  # type: ignore[arg-type]
        completed_modules=completed_count,
    )
