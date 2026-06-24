"""Sage — a standalone one-instructor mini-LMS with LMS Bridge built in (sage.lmsbridge.app).

No LMS, no LTI: an instructor signs up, creates a course, authors multiple-choice quizzes,
and shares a join code. Students join, take quizzes, and when they slip on a concept the
platform's existing adaptive engine (mastery + remediation + AI tutor) kicks in automatically.

Reuses the platform Course / Enrollment / Concept / Assessment / Question / result-ingestion.
"""
from __future__ import annotations

import io
import json
import re
import secrets

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, hash_password
from app.db.session import get_db
from app.models.assessment import Assessment, AssessmentResult, Question
from app.models.concept import Concept
from app.models.course import Course, Enrollment
from app.models.enums import AssessmentType, RemediationStatus, UserRole
from app.models.material import CourseMaterial
from app.models.remediation import RemediationModule
from app.models.user import User
from app.schemas.sage import (
    CourseCreate,
    JoinByCode,
    MaterialTextCreate,
    ProfileUpdate,
    QuizCreate,
    QuizSubmit,
    SageAuthOut,
    SageGuestJoin,
    SageJoinSignup,
    SageSignup,
    SyllabusUpdate,
)
from app.services.ingestion_service import ingest_result
from app.services.material_service import MAX_UPLOAD_BYTES, create_material

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
    out = _course_summary(db, course, role)
    out["syllabus"] = course.syllabus
    owner = db.get(User, course.owner_id) if course.owner_id else None
    out["instructor"] = ({
        "full_name": owner.full_name, "title": owner.title, "bio": owner.bio,
    } if owner else None)
    return out


# ------------------------------------------------------------- instructor profile

@router.get("/me")
def my_profile(user: User = Depends(get_current_user)) -> dict:
    return {"id": user.id, "full_name": user.full_name, "email": user.email,
            "title": user.title, "bio": user.bio}


@router.put("/me")
def update_profile(
    payload: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.title is not None:
        user.title = payload.title.strip() or None
    if payload.bio is not None:
        user.bio = payload.bio.strip() or None
    db.commit()
    db.refresh(user)
    return {"id": user.id, "full_name": user.full_name, "email": user.email,
            "title": user.title, "bio": user.bio}


@router.put("/courses/{course_id}/syllabus")
def update_syllabus(
    course_id: int, payload: SyllabusUpdate,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
) -> dict:
    course, role = _require_role(db, course_id, user)
    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    course.syllabus = payload.syllabus.strip() or None
    db.commit()
    return {"syllabus": course.syllabus}


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


_QTYPES = {"mcq", "true_false", "multi", "short"}


def _build_question(db: Session, assessment_id: int, course_id: int, q) -> Question:
    qtype = q.qtype if q.qtype in _QTYPES else "mcq"
    correct = q.correct if isinstance(q.correct, list) else [q.correct]
    correct = [c.strip() for c in correct if c and c.strip()]
    if not correct:
        raise HTTPException(status_code=400, detail=f"Question needs a correct answer: {q.prompt}")
    choices = [c.strip() for c in (q.choices or []) if c and c.strip()]
    if qtype == "true_false":
        choices = ["True", "False"]
    if qtype in ("mcq", "true_false", "multi"):
        if len(choices) < 2:
            raise HTTPException(status_code=400, detail=f"Question needs 2+ choices: {q.prompt}")
        if not all(c in choices for c in correct):
            raise HTTPException(status_code=400,
                                detail=f"Correct answer must be one of the choices: {q.prompt}")
        if qtype in ("mcq", "true_false") and len(correct) != 1:
            raise HTTPException(status_code=400,
                                detail=f"This type needs exactly one correct answer: {q.prompt}")
    else:  # short answer
        choices = []
    concept = _get_or_create_concept(db, course_id, q.concept)
    correct_answer = json.dumps(correct) if qtype in ("multi", "short") else correct[0]
    return Question(
        assessment_id=assessment_id, concept_id=concept.id, prompt=q.prompt.strip(),
        max_points=1.0, qtype=qtype, choices=choices or None, correct_answer=correct_answer)


def _correct_list(q: Question) -> list[str]:
    if (q.qtype or "mcq") in ("multi", "short"):
        try:
            v = json.loads(q.correct_answer or "[]")
            return [str(x) for x in v] if isinstance(v, list) else [str(v)]
        except Exception:  # noqa: BLE001
            return [q.correct_answer] if q.correct_answer else []
    return [q.correct_answer] if q.correct_answer else []


def _grade(q: Question, ans) -> tuple[bool, str]:
    """Return (is_correct, selected_display) for one answered question."""
    qtype = q.qtype or "mcq"
    if qtype == "multi":
        selected = set(ans.choices or ([ans.choice] if ans.choice else []))
        correct = set(_correct_list(q))
        return (bool(correct) and selected == correct, ", ".join(sorted(selected)))
    if qtype == "short":
        sel = (ans.choice or "").strip()
        accepted = {a.strip().lower() for a in _correct_list(q)}
        return (bool(accepted) and sel.lower() in accepted, sel)
    sel = ans.choice
    return (sel is not None and sel == q.correct_answer, sel or "")


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
        db.add(_build_question(db, quiz.id, course_id, q))
    db.commit()
    db.refresh(quiz)
    return {"id": quiz.id, "title": quiz.title, "question_count": len(payload.questions)}


@router.put("/quizzes/{quiz_id}")
def update_quiz(
    quiz_id: int, payload: QuizCreate,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
) -> dict:
    quiz = db.get(Assessment, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _course, role = _require_role(db, quiz.course_id, user)
    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    quiz.title = payload.title.strip()
    quiz.max_score = float(len(payload.questions))
    for old in db.scalars(select(Question).where(Question.assessment_id == quiz.id)).all():
        db.delete(old)
    db.flush()
    for q in payload.questions:
        db.add(_build_question(db, quiz.id, quiz.course_id, q))
    db.commit()
    return {"id": quiz.id, "title": quiz.title, "question_count": len(payload.questions)}


@router.delete("/quizzes/{quiz_id}", status_code=204)
def delete_quiz(
    quiz_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    quiz = db.get(Assessment, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _course, role = _require_role(db, quiz.course_id, user)
    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    db.delete(quiz)
    db.commit()


@router.post("/quizzes/{quiz_id}/duplicate", status_code=201)
def duplicate_quiz(
    quiz_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    quiz = db.get(Assessment, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _course, role = _require_role(db, quiz.course_id, user)
    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    questions = db.scalars(select(Question).where(Question.assessment_id == quiz.id)).all()
    copy = Assessment(course_id=quiz.course_id, title=f"{quiz.title} (copy)",
                      type=AssessmentType.quiz, max_score=quiz.max_score)
    db.add(copy)
    db.flush()
    for q in questions:
        db.add(Question(assessment_id=copy.id, concept_id=q.concept_id, prompt=q.prompt,
                        max_points=q.max_points, qtype=q.qtype, choices=q.choices,
                        correct_answer=q.correct_answer))
    db.commit()
    db.refresh(copy)
    return {"id": copy.id, "title": copy.title, "question_count": len(questions)}


@router.get("/quizzes/{quiz_id}/edit")
def quiz_for_edit(
    quiz_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    """Full quiz (with correct answers) for the instructor's edit form."""
    quiz = db.get(Assessment, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    _course, role = _require_role(db, quiz.course_id, user)
    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    questions = db.scalars(select(Question).where(Question.assessment_id == quiz.id)).all()
    return {
        "id": quiz.id, "title": quiz.title,
        "questions": [{
            "prompt": q.prompt, "qtype": q.qtype or "mcq", "choices": q.choices or [],
            "correct": _correct_list(q),
            "concept": (db.get(Concept, q.concept_id).name if q.concept_id else ""),
        } for q in questions],
    }


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
        "questions": [{"id": q.id, "prompt": q.prompt, "qtype": q.qtype or "mcq",
                       "choices": q.choices or []} for q in questions],
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
    answers = {a.question_id: a for a in payload.answers}

    item_scores: list[dict] = []
    review: list[dict] = []
    correct_n = 0
    for q in questions:
        ans = answers.get(q.id)
        is_correct, selected = _grade(q, ans) if ans else (False, "")
        if is_correct:
            correct_n += 1
        concept = db.get(Concept, q.concept_id) if q.concept_id else None
        correct_disp = ", ".join(_correct_list(q))
        item_scores.append({
            "question_id": q.id, "concept_key": concept.key if concept else None,
            "earned": 1.0 if is_correct else 0.0, "max": 1.0,
            "question": q.prompt, "choices": q.choices or [],
            "selected": selected, "correct": correct_disp, "is_correct": is_correct,
        })
        review.append({"question_id": q.id, "is_correct": is_correct,
                       "correct": correct_disp, "selected": selected})

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


# ------------------------------------------------------------- materials (notes / code / files)

def _material_out(m: CourseMaterial) -> dict:
    return {"id": m.id, "kind": m.kind, "title": m.title, "filename": m.filename,
            "content_type": m.content_type, "size_bytes": m.size_bytes,
            "language": m.language, "has_text": bool(m.extracted_text),
            "created_at": m.created_at}


@router.get("/courses/{course_id}/materials")
def list_course_materials(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[dict]:
    _require_role(db, course_id, user)
    rows = db.scalars(
        select(CourseMaterial).where(CourseMaterial.course_id == course_id)
        .order_by(CourseMaterial.created_at.desc())
    ).all()
    return [_material_out(m) for m in rows]


@router.post("/courses/{course_id}/materials/text", status_code=201)
def add_text_material(
    course_id: int, payload: MaterialTextCreate,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
) -> dict:
    course, role = _require_role(db, course_id, user)
    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    kind = payload.kind if payload.kind in ("note", "code") else "note"
    ext = ".md" if kind == "note" else ".txt"
    content_type = "text/markdown" if kind == "note" else "text/plain"
    m = create_material(
        db, course_id=course.id, title=payload.title.strip(),
        filename=f"{_slug(payload.title)}{ext}", content_type=content_type,
        data=payload.body.encode("utf-8"), uploaded_by=user.id,
    )
    m.kind = kind
    m.language = (payload.language or None) if kind == "code" else None
    db.commit()
    db.refresh(m)
    return _material_out(m)


@router.post("/courses/{course_id}/materials/file", status_code=201)
async def upload_file_material(
    course_id: int,
    title: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    course, role = _require_role(db, course_id, user)
    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit")
    m = create_material(
        db, course_id=course.id, title=title.strip() or file.filename or "Untitled",
        filename=file.filename or "upload", content_type=file.content_type or "",
        data=data, uploaded_by=user.id,
    )
    m.kind = "file"
    db.commit()
    db.refresh(m)
    return _material_out(m)


@router.get("/materials/{material_id}")
def get_material(
    material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> dict:
    m = db.get(CourseMaterial, material_id)
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")
    _require_role(db, m.course_id, user)
    out = _material_out(m)
    out["body"] = (m.content.decode("utf-8", errors="replace")
                   if m.kind in ("note", "code") and m.content is not None else None)
    return out


@router.get("/materials/{material_id}/download")
def download_material(
    material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> StreamingResponse:
    m = db.get(CourseMaterial, material_id)
    if not m or m.content is None:
        raise HTTPException(status_code=404, detail="Material not found")
    _require_role(db, m.course_id, user)
    return StreamingResponse(
        io.BytesIO(m.content), media_type=m.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{m.filename}"'})


@router.delete("/materials/{material_id}", status_code=204)
def delete_material(
    material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    m = db.get(CourseMaterial, material_id)
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")
    _course, role = _require_role(db, m.course_id, user)
    if role != "instructor":
        raise HTTPException(status_code=403, detail="Instructors only")
    db.delete(m)
    db.commit()
