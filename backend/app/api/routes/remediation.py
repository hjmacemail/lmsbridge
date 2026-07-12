from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, require_instructor
from app.db.session import get_db
from app.models.concept import Concept
from app.models.course import Course
from app.models.enums import PedagogyStrategy, RemediationStatus, UserRole
from app.models.mastery import ConceptMastery
from app.models.remediation import RemediationActivity, RemediationModule
from app.models.user import User
from app.schemas.remediation import (
    GenerateRemediationRequest,
    RemediationModuleOut,
    ResponseFeedbackOut,
    SessionMessageRequest,
    SessionState,
    SessionTurnOut,
    SubmitResponseRequest,
)
from app.services.remediation_engine import evaluate_response, generate_module
from app.services.tutor_session_service import (
    post_message,
    session_context,
    start_session,
)

router = APIRouter(prefix="/remediation", tags=["remediation"])


def _load_module(db: Session, module_id: int) -> RemediationModule:
    module = db.scalar(
        select(RemediationModule)
        .where(RemediationModule.id == module_id)
        .options(
            selectinload(RemediationModule.activities),
            selectinload(RemediationModule.messages),
        )
    )
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    return module


def _session_state(db: Session, module: RemediationModule) -> SessionState:
    ctx = session_context(db, module)
    return SessionState(
        module_id=module.id,
        title=module.title,
        concept_id=module.concept_id,
        status=module.status,
        rationale=module.rationale,
        grounded_on=module.grounded_on,
        messages=module.messages,  # type: ignore[arg-type]
        **ctx,
    )


def _authorize(user: User, module: RemediationModule) -> None:
    if user.role == UserRole.student and module.student_id != user.id:
        raise HTTPException(status_code=403, detail="Not your remediation module")


@router.get("/modules", response_model=list[RemediationModuleOut])
def my_modules(
    status: RemediationStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[RemediationModule]:
    stmt = select(RemediationModule).options(selectinload(RemediationModule.activities))
    if user.role == UserRole.student:
        stmt = stmt.where(RemediationModule.student_id == user.id)
    if status:
        stmt = stmt.where(RemediationModule.status == status)
    return list(db.scalars(stmt.order_by(RemediationModule.created_at.desc())).all())


@router.get("/modules/{module_id}", response_model=RemediationModuleOut)
def get_module(
    module_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> RemediationModule:
    module = _load_module(db, module_id)
    _authorize(user, module)
    return module


# ---- Interactive AI-tutor session ----

@router.get("/modules/{module_id}/session", response_model=SessionState)
def get_session(
    module_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> SessionState:
    """Fetch the current session transcript + status (does not create the opening turn)."""
    module = _load_module(db, module_id)
    _authorize(user, module)
    return _session_state(db, module)


@router.post("/modules/{module_id}/session/start", response_model=SessionState)
def start_session_endpoint(
    module_id: int, lang: str | None = None,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
) -> SessionState:
    """Begin (or resume) the tutoring session — generates the opening turn if needed."""
    module = _load_module(db, module_id)
    _authorize(user, module)
    module = start_session(db, module, language=lang)
    return _session_state(db, module)


@router.post("/modules/{module_id}/session/message", response_model=SessionTurnOut)
def send_session_message(
    module_id: int,
    payload: SessionMessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SessionTurnOut:
    """Send the student's message and get the tutor's next turn (+ completion signal)."""
    module = _load_module(db, module_id)
    _authorize(user, module)
    if module.status == RemediationStatus.completed:
        raise HTTPException(status_code=409, detail="This session is already complete")
    if not (payload.text or "").strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    result = post_message(db, module, payload.text.strip(), language=payload.lang)
    return SessionTurnOut(**result)


@router.post("/modules/{module_id}/start", response_model=RemediationModuleOut)
def start_module(
    module_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> RemediationModule:
    module = _load_module(db, module_id)
    _authorize(user, module)
    if module.status == RemediationStatus.pending:
        module.status = RemediationStatus.in_progress
        db.commit()
        db.refresh(module)
    return module


@router.post("/activities/{activity_id}/respond", response_model=ResponseFeedbackOut)
def respond(
    activity_id: int,
    payload: SubmitResponseRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ResponseFeedbackOut:
    activity = db.scalar(
        select(RemediationActivity)
        .where(RemediationActivity.id == activity_id)
        .options(selectinload(RemediationActivity.module))
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    _authorize(user, activity.module)
    sr = evaluate_response(
        db, activity=activity, student_id=activity.module.student_id,
        response_text=payload.response_text,
    )
    db.commit()
    db.refresh(sr)
    return sr


@router.post("/modules/{module_id}/complete", response_model=RemediationModuleOut)
def complete_module(
    module_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> RemediationModule:
    module = _load_module(db, module_id)
    _authorize(user, module)
    module.status = RemediationStatus.completed
    module.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(module)
    return module


@router.post(
    "/generate",
    response_model=RemediationModuleOut,
    dependencies=[Depends(require_instructor)],
)
def generate(
    payload: GenerateRemediationRequest, db: Session = Depends(get_db)
) -> RemediationModule:
    """Instructor-triggered manual remediation generation for a student + concept."""
    concept = db.get(Concept, payload.concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")
    course = db.get(Course, concept.course_id)
    mastery = db.scalar(
        select(ConceptMastery).where(
            ConceptMastery.student_id == payload.student_id,
            ConceptMastery.concept_id == payload.concept_id,
        )
    )
    module = generate_module(
        db,
        student_id=payload.student_id,
        course_id=concept.course_id,
        concept=concept,
        course_title=course.title if course else "",
        mastery_score=mastery.mastery_score if mastery else 0.5,
        strategy=payload.strategy or PedagogyStrategy.socratic_scaffolding,
    )
    db.commit()
    db.refresh(module)
    return module
