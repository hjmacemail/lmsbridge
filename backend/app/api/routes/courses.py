from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_instructor
from app.db.session import get_db
from app.models.assessment import Assessment
from app.models.concept import Concept
from app.models.course import Course, Enrollment
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.assessment import AssessmentOut
from app.schemas.course import (
    AssessmentCreate,
    ConceptCreate,
    ConceptOut,
    ConceptUpdate,
    CourseCreate,
    CourseDetail,
    CourseOut,
    CourseUpdate,
)

router = APIRouter(prefix="/courses", tags=["courses"])


def _concept_out(c: Concept) -> ConceptOut:
    return ConceptOut(
        id=c.id, key=c.key, name=c.name, description=c.description, sequence=c.sequence,
        common_misconceptions=c.common_misconceptions,
        prerequisite_keys=[p.key for p in c.prerequisites],
    )


def _load_course(db: Session, course_id: int) -> Course:
    course = db.scalar(
        select(Course).where(Course.id == course_id).options(selectinload(Course.concepts))
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


# ---- Read ----

@router.get("", response_model=list[CourseOut])
def list_courses(
    db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[Course]:
    return list(db.scalars(select(Course).order_by(Course.code)).all())


@router.get("/{course_id}", response_model=CourseDetail)
def get_course(
    course_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> CourseDetail:
    course = _load_course(db, course_id)
    concepts = sorted(course.concepts, key=lambda c: c.sequence)
    return CourseDetail(
        id=course.id, code=course.code, title=course.title, term=course.term,
        brightspace_course_id=course.brightspace_course_id,
        concepts=[_concept_out(c) for c in concepts],
    )


# ---- Manual management (instructor / admin) ----

@router.post("", response_model=CourseOut, status_code=201)
def create_course(
    payload: CourseCreate, db: Session = Depends(get_db),
    user: User = Depends(require_instructor),
) -> Course:
    """Create a course by hand (for pilots without an LMS). Enrolls the creator."""
    existing = db.scalar(
        select(Course).where(Course.code == payload.code, Course.term == payload.term)
    )
    if existing:
        raise HTTPException(status_code=409, detail="A course with that code + term exists")
    course = Course(
        code=payload.code, title=payload.title, term=payload.term, tenant_id=user.tenant_id,
    )
    db.add(course)
    db.flush()
    db.add(Enrollment(user_id=user.id, course_id=course.id, role=UserRole.instructor))
    db.commit()
    db.refresh(course)
    return course


@router.put("/{course_id}", response_model=CourseOut)
def update_course(
    course_id: int, payload: CourseUpdate, db: Session = Depends(get_db),
    _: User = Depends(require_instructor),
) -> Course:
    course = _load_course(db, course_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


def _set_prerequisites(db: Session, course: Course, concept: Concept, keys: list[str]) -> None:
    if not keys:
        concept.prerequisites = []
        return
    rows = db.scalars(
        select(Concept).where(Concept.course_id == course.id, Concept.key.in_(keys))
    ).all()
    concept.prerequisites = [c for c in rows if c.id != concept.id]


@router.post("/{course_id}/concepts", response_model=ConceptOut, status_code=201)
def add_concept(
    course_id: int, payload: ConceptCreate, db: Session = Depends(get_db),
    _: User = Depends(require_instructor),
) -> ConceptOut:
    course = _load_course(db, course_id)
    if db.scalar(
        select(Concept).where(Concept.course_id == course.id, Concept.key == payload.key)
    ):
        raise HTTPException(status_code=409, detail="Concept key already exists in this course")
    concept = Concept(
        course_id=course.id, key=payload.key, name=payload.name,
        description=payload.description, sequence=payload.sequence,
        common_misconceptions=payload.common_misconceptions,
    )
    db.add(concept)
    db.flush()
    _set_prerequisites(db, course, concept, payload.prerequisite_keys)
    db.commit()
    db.refresh(concept)
    return _concept_out(concept)


@router.put("/{course_id}/concepts/{concept_id}", response_model=ConceptOut)
def update_concept(
    course_id: int, concept_id: int, payload: ConceptUpdate, db: Session = Depends(get_db),
    _: User = Depends(require_instructor),
) -> ConceptOut:
    course = _load_course(db, course_id)
    concept = db.get(Concept, concept_id)
    if not concept or concept.course_id != course.id:
        raise HTTPException(status_code=404, detail="Concept not found")
    data = payload.model_dump(exclude_unset=True)
    prereqs = data.pop("prerequisite_keys", None)
    for field, value in data.items():
        setattr(concept, field, value)
    if prereqs is not None:
        _set_prerequisites(db, course, concept, prereqs)
    db.commit()
    db.refresh(concept)
    return _concept_out(concept)


@router.delete("/{course_id}/concepts/{concept_id}", status_code=204)
def delete_concept(
    course_id: int, concept_id: int, db: Session = Depends(get_db),
    _: User = Depends(require_instructor),
) -> None:
    concept = db.get(Concept, concept_id)
    if not concept or concept.course_id != course_id:
        raise HTTPException(status_code=404, detail="Concept not found")
    db.delete(concept)
    db.commit()


@router.post("/{course_id}/assessments", response_model=AssessmentOut, status_code=201)
def create_assessment(
    course_id: int, payload: AssessmentCreate, db: Session = Depends(get_db),
    _: User = Depends(require_instructor),
) -> Assessment:
    _load_course(db, course_id)
    assessment = Assessment(
        course_id=course_id, title=payload.title, type=payload.type,
        max_score=payload.max_score,
        available_at=payload.available_at or datetime.now(timezone.utc),
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment
