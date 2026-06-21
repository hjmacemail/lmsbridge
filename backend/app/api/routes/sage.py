"""Sage — a standalone one-instructor mini-LMS with LMS Bridge built in (sage.lmsbridge.app).

No LMS, no LTI: an instructor signs up, creates a course, authors multiple-choice quizzes,
and shares a join code. Students join, take quizzes, and when they slip on a concept the
platform's existing adaptive engine (mastery + remediation + AI tutor) kicks in automatically.

Reuses the platform Course / Enrollment / Concept / Assessment / Question / result-ingestion.
"""
from __future__ import annotations

import re
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.models.assessment import Assessment, AssessmentResult, Question
from app.models.concept import Concept
from app.models.course import Course, Enrollment
from app.models.enums import AssessmentType, RemediationStatus, UserRole
from app.models.remediation import RemediationModule
from app.models.user import User
from app.schemas.sage import (
    CourseCreate,
    JoinByCode,
    QuizCreate,
    QuizSubmit,
    SageAuthOut,
    SageGuestJoin,
    SageJoinSignup,
    SageSignup,
)
from app.services.ingestion_service import ingest_result

router = APIRouter(prefix="/sage", tags=["sage"])

_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _gen_join_code(db: Session) -> str:
    for _ in range(20):
        code = "".join(secrets.choice(_ALPHABET) for _ in range(6))
        if not db.scalar(select(Course).where(Course.join_code == code)):
            return code
    raise HTTPException(status_code=500, detail="Could not allocate a join code")


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_") or "concept"


def _auth_out(user: User) -> SageAuthOut:
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return SageAuthOut(access_token=token, user_id=user.id,
                       full_name=user.full_name, role=user.role.value)


def _course_by_code(db: Session, code: str) -> Course:
    c = db.scalar(select(Course).where(Course.join_code == code.strip().upper()))
    if not c:
        raise HTTPException(status_code=404, detail="No course with that join code")
    return c


def _enroll(db: Session, course: Course, user: User, role: UserRole) -> None:
    exists = db.scalar(select(Enrollment).where(
        Enrollment.user_id == user.id, Enrollment.course_id == course.id))
    if not exists:
        db.add(Enrollment(user_id=user.id, course_id=course.id, role=role))


def _role_in(db: Session, course: Course, user: User) -> str | None:
    if course.owner_id == user.id:
        return "instructor"
    enr = db.scalar(select(Enrollment).where(
        Enrollment.user_id == user.id, Enrollment.course_id == course.id))
    if not enr:
        return None
    return "instructor" if enr.role in (UserRole.instructor, UserRole.admin) else "student"


def _require_role(db: Session, course_id: int, user: User) -> tuple[Course, str]:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    role = _role_in(db, course, user)
    if role is None:
        raise HTTPException(status_code=403, detail="You are not a member of this course")
    return course, role


# ------------------------------------------------------------- auth / onboarding

@router.post("/signup", response_model=SageAuthOut, status_code=201)
def signup(payload: SageSignup, db: Session = Depends(get_db)) -> SageAuthOut:
    email = payload.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    user = User(email=email, full_name=payload.full_name.strip(), role=UserRole.instructor,
                hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _auth_out(user)


@router.post("/join", response_model=SageAuthOut, status_code=201)
def join_with_signup(payload: SageJoinSignup, db: Session = Depends(get_db)) -> SageAuthOut:
    course = _course_by_code(db, payload.join_code)
    email = payload.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="An account with that email already exists")
    user = User(email=email, full_name=payload.full_name.strip(), role=UserRole.student,
                hashed_password=hash_password(payload.password))
    db.add(user)
    db.flush()
    _enroll(db, course, user, UserRole.student)
    db.commit()
    db.refresh(user)
    return _auth_out(user)


@router.post("/guest", response_model=SageAuthOut, status_code=201)
def guest_join(payload: SageGuestJoin, db: Session = Depends(get_db)) -> SageAuthOut:
    course = _course_by_code(db, payload.join_code)
    user = User(email=f"guest-{secrets.token_hex(8)}@sage.local",
                full_name=payload.full_name.strip(), role=UserRole.student,
                hashed_password=hash_password(secrets.token_urlsafe(24)))
    db.add(user)
    db.flush()
    _enroll(db, course, user, UserRole.student)
    db.commit()
    db.refresh(user)
    return _auth_out(user)


@router.post("/courses/join")
def join_existing(
    payload: JoinByCode, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    course = _course_by_code(db, payload.join_code)
    _enroll(db, course, user, UserRole.student)
    db.commit()
    return {"course_id": course.id, "name": course.title}


# ------------------------------------------------------------- courses

def _course_summary(db: Session, c: Course, role: str) -> dict:
    students = db.scalar(select(func.count(Enrollment.id)).where(
        Enrollment.course_id == c.id, Enrollment.role == UserRole.student)) or 0
    quizzes = db.scalar(select(func.count(Assessment.id)).where(Assessment.course_id == c.id)) or 0
    return {
        "id": c.id, "name": c.title, "role": role, "join_code": c.join_code,
        "student_count": students, "quiz_count": quizzes,
    }


@router.post("/courses", status_code=201)
def create_course(
    payload: CourseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    code = _gen_join_code(db)
    course = Course(
        code=f"{payload.name.strip()[:40]} [{code}]", title=payload.name.strip(),
        term="Sage", join_code=code, owner_id=user.id,
    )
    db.add(course)
    db.flush()
    _enroll(db, course, user, UserRole.instructor)
    db.commit()
    db.refresh(course)
    return _course_summary(db, course, "instructor")


@router.get("/courses")
def my_courses(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    owned = db.scalars(select(Course).where(Course.owner_id == user.id)).all()
    enrolled = db.execute(
        select(Course).join(Enrollment, Enrollment.course_id == Course.id)
        .where(Enrollment.user_id == user.id)
    ).scalars().all()
    seen: dict[int, Course] = {}
    for c in [*owned, *enrolled]:
        seen.setdefault(c.id, c)
    out = []
    for c in seen.values():
        role = _role_in(db, c, user) or "student"
        out.append(_course_summary(db, c, role))
    return sorted(out, key=lambda x: x["id"], reverse=True)


@router.get("/courses/{course_id}")
def course_detail(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    course, role = _require_role(db, course_id, user)
    return _course_summary(db, course, role)


@router.get("/courses/{course_id}/students")
def course_students(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict]:
    _course, role = _require_role(db, course_id, user)
    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    rows = db.execute(
        select(User).join(Enrollment, Enrollment.user_id == User.id)
        .where(Enrollment.course_id == course_id, Enrollment.role == UserRole.student)
        .order_by(User.full_name)
    ).scalars().all()
    return [{"id": u.id, "full_name": u.full_name, "email": u.email} for u in rows]


# ------------------------------------------------------------- quizzes

def _get_or_create_concept(db: Session, course_id: int, name: str) -> Concept:
    key = _slug(name)
    c = db.scalar(select(Concept).where(Concept.course_id == course_id, Concept.key == key))
    if not c:
        c = Concept(course_id=course_id, key=key, name=name.strip())
        db.add(c)
        db.flush()
    return c


@router.post("/courses/{course_id}/quizzes", status_code=201)
def create_quiz(
    course_id: int, payload: QuizCreate,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
) -> dict:
    _course, role = _require_role(db, course_id, user)
    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    quiz = Assessment(course_id=course_id, title=payload.title.strip(),
                      type=AssessmentType.quiz, max_score=float(len(payload.questions)))
    db.add(quiz)
    db.flush()
    for q in payload.questions:
        if q.correct not in q.choices:
            raise HTTPException(status_code=400,
                                detail=f"Correct answer must be one of the choices for: {q.prompt}")
        concept = _get_or_create_concept(db, course_id, q.concept)
        db.add(Question(assessment_id=quiz.id, concept_id=concept.id, prompt=q.prompt,
                        max_points=1.0, choices=q.choices, correct_answer=q.correct))
    db.commit()
    db.refresh(quiz)
    return {"id": quiz.id, "title": quiz.title, "question_count": len(payload.questions)}


@router.get("/courses/{course_id}/quizzes")
def list_quizzes(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict]:
    _course, role = _require_role(db, course_id, user)
    quizzes = db.scalars(
        select(Assessment).where(Assessment.course_id == course_id)
        .order_by(Assessment.created_at.desc())
    ).all()
    out = []
    for a in quizzes:
        qn = db.scalar(select(func.count(Question.id)).where(Question.assessment_id == a.id)) or 0
        item = {"id": a.id, "title": a.title, "question_count": qn}
        if role == "instructor":
            item["submission_count"] = db.scalar(select(func.count(AssessmentResult.id)).where(
                AssessmentResult.assessment_id == a.id)) or 0
        else:
            last = db.scalar(
                select(AssessmentResult).where(
                    AssessmentResult.assessment_id == a.id,
                    AssessmentResult.student_id == user.id)
                .order_by(AssessmentResult.created_at.desc()))
            item["my_score"] = round(last.score, 2) if last else None
        out.append(item)
    return out


@router.get("/quizzes/{quiz_id}/take")
def take_quiz(
    quiz_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    quiz = db.get(Assessment, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _require_role(db, quiz.course_id, user)
    questions = db.scalars(select(Question).where(Question.assessment_id == quiz_id)).all()
    return {
        "id": quiz.id, "title": quiz.title,
        "questions": [{"id": q.id, "prompt": q.prompt, "choices": q.choices or []}
                      for q in questions],
    }


@router.post("/quizzes/{quiz_id}/submit")
def submit_quiz(
    quiz_id: int, payload: QuizSubmit,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
) -> dict:
    quiz = db.get(Assessment, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _require_role(db, quiz.course_id, user)
    questions = db.scalars(select(Question).where(Question.assessment_id == quiz_id)).all()
    chosen = {a.question_id: a.choice for a in payload.answers}

    item_scores: list[dict] = []
    review: list[dict] = []
    correct_n = 0
    for q in questions:
        sel = chosen.get(q.id)
        is_correct = sel is not None and sel == q.correct_answer
        if is_correct:
            correct_n += 1
        concept = db.get(Concept, q.concept_id) if q.concept_id else None
        item_scores.append({
            "question_id": q.id, "concept_key": concept.key if concept else None,
            "earned": 1.0 if is_correct else 0.0, "max": 1.0,
            "question": q.prompt, "choices": q.choices or [],
            "selected": sel, "correct": q.correct_answer, "is_correct": is_correct,
        })
        review.append({"question_id": q.id, "is_correct": is_correct,
                       "correct": q.correct_answer, "selected": sel})

    total = len(questions) or 1
    score = correct_n / total
    _result, modules = ingest_result(
        db, assessment=quiz, student=user, score=score, item_scores=item_scores)

    return {
        "score": round(score, 3), "correct": correct_n, "total": len(questions),
        "review": review, "remediation_created": len(modules),
    }


# ------------------------------------------------------------- grades

@router.get("/courses/{course_id}/grades")
def grades(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    course, role = _require_role(db, course_id, user)
    quizzes = db.scalars(select(Assessment).where(Assessment.course_id == course_id)).all()
    quiz_titles = [{"id": a.id, "title": a.title} for a in quizzes]

    def best_scores(student_id: int) -> dict[int, float]:
        out: dict[int, float] = {}
        for a in quizzes:
            r = db.scalar(
                select(func.max(AssessmentResult.score)).where(
                    AssessmentResult.assessment_id == a.id,
                    AssessmentResult.student_id == student_id))
            if r is not None:
                out[a.id] = round(r, 2)
        return out

    def open_remediation(student_id: int) -> int:
        return db.scalar(select(func.count(RemediationModule.id)).where(
            RemediationModule.student_id == student_id,
            RemediationModule.course_id == course_id,
            RemediationModule.status.in_(
                [RemediationStatus.pending, RemediationStatus.in_progress]))) or 0

    if role == "instructor":
        students = db.execute(
            select(User).join(Enrollment, Enrollment.user_id == User.id)
            .where(Enrollment.course_id == course_id, Enrollment.role == UserRole.student)
            .order_by(User.full_name)
        ).scalars().all()
        rows = [{
            "student_id": s.id, "full_name": s.full_name,
            "scores": best_scores(s.id), "open_remediation": open_remediation(s.id),
        } for s in students]
        return {"quizzes": quiz_titles, "rows": rows, "is_instructor": True}

    return {
        "quizzes": quiz_titles,
        "scores": best_scores(user.id),
        "open_remediation": open_remediation(user.id),
        "is_instructor": False,
    }
