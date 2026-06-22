from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_instructor, require_role
from app.db.session import get_db
from app.models.assessment import Assessment, AssessmentResult
from app.models.concept import Concept
from app.models.course import Course, Enrollment
from app.models.enums import MasteryStatus, RemediationStatus, UserRole
from app.models.lti import LtiRegistration
from app.models.mastery import ConceptMastery
from app.models.remediation import RemediationActivity, RemediationModule
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.analytics import (
    ActivityWithResponses,
    AssessmentBreakdown,
    ConceptStat,
    InstitutionCourseRow,
    InstitutionUsage,
    ModuleSummary,
    ModuleWithStudent,
    ResponseDetail,
    ResultDetail,
    RosterEntry,
    StudentDetail,
    TranscriptTurn,
)
from app.schemas.remediation import ConceptRisk, InstructorAnalytics, MasteryOut
from app.services.course_access import require_course_instructor

router = APIRouter(prefix="/analytics", tags=["analytics"])
require_admin = require_role(UserRole.admin)


def _lms_connected(db: Session) -> bool:
    return bool(
        db.scalar(
            select(func.count(LtiRegistration.id)).where(LtiRegistration.active.is_(True))
        )
    )


def _tenant_course_ids(db: Session, admin: User) -> list[int]:
    """Course ids visible to this admin's institution.

    Scoped by tenant when the admin has one. The lowest-id tenant also absorbs legacy
    courses with no tenant set (single-institution / pre-multitenant seed data). With no
    tenant at all, fall back to every course (single-institution deployment).
    """
    q = select(Course.id)
    if admin.tenant_id:
        lowest = db.scalar(select(func.min(Tenant.id)))
        if admin.tenant_id == lowest:
            q = q.where(
                or_(Course.tenant_id == admin.tenant_id, Course.tenant_id.is_(None))
            )
        else:
            q = q.where(Course.tenant_id == admin.tenant_id)
    return list(db.scalars(q).all())


@router.get("/institution", response_model=InstitutionUsage)
def institution_usage(
    db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> InstitutionUsage:
    """Aggregate adoption metrics for the institution/IT admin — no student-level data."""
    tenant = None
    if admin.tenant_id:
        tenant = db.get(Tenant, admin.tenant_id)
    if tenant is None:
        tenant = db.scalar(select(Tenant).order_by(Tenant.id))
    tenant_name = tenant.name if tenant else "Your institution"

    course_ids = _tenant_course_ids(db, admin)
    if not course_ids:
        return InstitutionUsage(
            tenant_name=tenant_name, lms_connected=_lms_connected(db), courses=0,
            students=0, instructors=0, sessions_started=0, modules_generated=0,
            modules_completed=0, completion_rate=0.0, course_rows=[],
        )

    students = db.scalar(
        select(func.count(func.distinct(Enrollment.user_id))).where(
            Enrollment.course_id.in_(course_ids), Enrollment.role == UserRole.student
        )
    ) or 0
    instructors = db.scalar(
        select(func.count(func.distinct(Enrollment.user_id))).where(
            Enrollment.course_id.in_(course_ids), Enrollment.role == UserRole.instructor
        )
    ) or 0
    generated = db.scalar(
        select(func.count(RemediationModule.id)).where(
            RemediationModule.course_id.in_(course_ids)
        )
    ) or 0
    completed = db.scalar(
        select(func.count(RemediationModule.id)).where(
            RemediationModule.course_id.in_(course_ids),
            RemediationModule.status == RemediationStatus.completed,
        )
    ) or 0
    sessions_started = db.scalar(
        select(func.count(RemediationModule.id)).where(
            RemediationModule.course_id.in_(course_ids),
            RemediationModule.status.in_(
                [RemediationStatus.in_progress, RemediationStatus.completed]
            ),
        )
    ) or 0

    rows: list[InstitutionCourseRow] = []
    for c in db.scalars(
        select(Course).where(Course.id.in_(course_ids)).order_by(Course.code)
    ).all():
        c_students = db.scalar(
            select(func.count(Enrollment.id)).where(
                Enrollment.course_id == c.id, Enrollment.role == UserRole.student
            )
        ) or 0
        c_done = db.scalar(
            select(func.count(RemediationModule.id)).where(
                RemediationModule.course_id == c.id,
                RemediationModule.status == RemediationStatus.completed,
            )
        ) or 0
        concept_ids = (
            select(Concept.id).where(Concept.course_id == c.id).scalar_subquery()
        )
        avg = db.scalar(
            select(func.avg(ConceptMastery.mastery_score)).where(
                ConceptMastery.concept_id.in_(concept_ids)
            )
        )
        rows.append(InstitutionCourseRow(
            course_id=c.id, code=c.code, title=c.title, students=c_students,
            modules_completed=c_done, avg_mastery=round(float(avg), 3) if avg else 0.0,
        ))

    return InstitutionUsage(
        tenant_name=tenant_name, lms_connected=_lms_connected(db),
        courses=len(course_ids), students=students, instructors=instructors,
        sessions_started=sessions_started, modules_generated=generated,
        modules_completed=completed,
        completion_rate=round(completed / generated, 3) if generated else 0.0,
        course_rows=rows,
    )


@router.get("/courses/{course_id}", response_model=InstructorAnalytics)
def course_analytics(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(require_instructor)
) -> InstructorAnalytics:
    course = require_course_instructor(db, course_id, user)

    enrolled = db.scalar(
        select(func.count(Enrollment.id)).where(
            Enrollment.course_id == course_id, Enrollment.role == UserRole.student
        )
    ) or 0

    risks: list[ConceptRisk] = []
    concepts = db.scalars(
        select(Concept).where(Concept.course_id == course_id).order_by(Concept.sequence)
    ).all()
    for c in concepts:
        rows = db.scalars(
            select(ConceptMastery).where(ConceptMastery.concept_id == c.id)
        ).all()
        if not rows:
            continue
        avg = sum(r.mastery_score for r in rows) / len(rows)
        at_risk = sum(1 for r in rows if r.status == MasteryStatus.at_risk)
        risks.append(
            ConceptRisk(
                concept_id=c.id, concept_key=c.key, concept_name=c.name,
                avg_mastery=round(avg, 3), at_risk_count=at_risk, total_students=len(rows),
            )
        )
    risks.sort(key=lambda r: r.avg_mastery)

    generated = db.scalar(
        select(func.count(RemediationModule.id)).where(RemediationModule.course_id == course_id)
    ) or 0
    completed = db.scalar(
        select(func.count(RemediationModule.id)).where(
            RemediationModule.course_id == course_id,
            RemediationModule.status == RemediationStatus.completed,
        )
    ) or 0

    return InstructorAnalytics(
        course_id=course.id, course_title=course.title, enrolled_students=enrolled,
        concept_risks=risks, modules_generated=generated, modules_completed=completed,
    )


def _require_course(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/courses/{course_id}/roster", response_model=list[RosterEntry])
def course_roster(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(require_instructor)
) -> list[RosterEntry]:
    """One row per enrolled student with a mastery + remediation summary."""
    require_course_instructor(db, course_id, user)
    students = db.scalars(
        select(User)
        .join(Enrollment, Enrollment.user_id == User.id)
        .where(Enrollment.course_id == course_id, Enrollment.role == UserRole.student)
        .order_by(User.full_name)
    ).all()

    concept_ids = select(Concept.id).where(Concept.course_id == course_id).scalar_subquery()
    entries: list[RosterEntry] = []
    for s in students:
        masteries = db.scalars(
            select(ConceptMastery).where(
                ConceptMastery.student_id == s.id,
                ConceptMastery.concept_id.in_(concept_ids),
            )
        ).all()
        avg = sum(m.mastery_score for m in masteries) / len(masteries) if masteries else 0.0
        at_risk = sum(1 for m in masteries if m.status == MasteryStatus.at_risk)
        open_n = db.scalar(
            select(func.count(RemediationModule.id)).where(
                RemediationModule.student_id == s.id,
                RemediationModule.course_id == course_id,
                RemediationModule.status.in_(
                    [RemediationStatus.pending, RemediationStatus.in_progress]
                ),
            )
        ) or 0
        done_n = db.scalar(
            select(func.count(RemediationModule.id)).where(
                RemediationModule.student_id == s.id,
                RemediationModule.course_id == course_id,
                RemediationModule.status == RemediationStatus.completed,
            )
        ) or 0
        entries.append(RosterEntry(
            student_id=s.id, full_name=s.full_name, email=s.email,
            avg_mastery=round(avg, 3), at_risk_concepts=at_risk,
            open_modules=open_n, completed_modules=done_n,
        ))
    return entries


@router.get("/courses/{course_id}/students/{student_id}", response_model=StudentDetail)
def student_detail(
    course_id: int, student_id: int,
    db: Session = Depends(get_db), user: User = Depends(require_instructor),
) -> StudentDetail:
    """Full drill-down: mastery, every assessment result, and remediation modules."""
    require_course_instructor(db, course_id, user)
    student = db.get(User, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    concept_by_id = {
        c.id: c for c in db.scalars(select(Concept).where(Concept.course_id == course_id)).all()
    }
    masteries = db.scalars(
        select(ConceptMastery).where(
            ConceptMastery.student_id == student_id,
            ConceptMastery.concept_id.in_(list(concept_by_id) or [-1]),
        )
    ).all()
    mastery_out = [
        MasteryOut(
            concept_id=m.concept_id,
            concept_key=concept_by_id[m.concept_id].key if m.concept_id in concept_by_id else None,
            concept_name=(concept_by_id[m.concept_id].name
                          if m.concept_id in concept_by_id else None),
            mastery_score=m.mastery_score, status=m.status, evidence_count=m.evidence_count,
        )
        for m in masteries
    ]

    results = db.scalars(
        select(AssessmentResult)
        .join(Assessment, Assessment.id == AssessmentResult.assessment_id)
        .where(AssessmentResult.student_id == student_id, Assessment.course_id == course_id)
        .options(selectinload(AssessmentResult.assessment))
        .order_by(AssessmentResult.ingested_at)
    ).all()
    result_out = [
        ResultDetail(
            id=r.id, assessment_id=r.assessment_id, assessment_title=r.assessment.title,
            assessment_type=r.assessment.type, score=r.score, attempts=r.attempts,
            time_on_task_minutes=r.time_on_task_minutes, submitted_late=r.submitted_late,
            rubric_feedback=r.rubric_feedback, item_scores=r.item_scores or [],
            rubric_criteria=r.rubric_criteria or [], created_at=r.created_at,
        )
        for r in results
    ]

    modules = db.scalars(
        select(RemediationModule)
        .where(RemediationModule.student_id == student_id,
               RemediationModule.course_id == course_id)
        .options(selectinload(RemediationModule.activities))
        .order_by(RemediationModule.created_at.desc())
    ).all()
    module_out = [
        ModuleSummary(
            id=m.id, concept_id=m.concept_id,
            concept_name=(concept_by_id[m.concept_id].name
                          if m.concept_id in concept_by_id else None),
            title=m.title, status=m.status, strategy=m.strategy.value,
            grounded_on=m.grounded_on, activity_count=len(m.activities),
            response_count=sum(len(a.responses) for a in m.activities), created_at=m.created_at,
        )
        for m in modules
    ]
    return StudentDetail(
        student_id=student.id, full_name=student.full_name, email=student.email,
        masteries=mastery_out, results=result_out, modules=module_out,
    )


@router.get("/courses/{course_id}/assessments", response_model=list[AssessmentBreakdown])
def assessment_breakdown(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(require_instructor)
) -> list[AssessmentBreakdown]:
    """Per-assessment, per-concept score distributions plus sample rubric feedback."""
    require_course_instructor(db, course_id, user)
    assessments = db.scalars(
        select(Assessment).where(Assessment.course_id == course_id)
        .order_by(Assessment.available_at)
    ).all()
    out: list[AssessmentBreakdown] = []
    for a in assessments:
        results = db.scalars(
            select(AssessmentResult).where(AssessmentResult.assessment_id == a.id)
        ).all()
        if not results:
            out.append(AssessmentBreakdown(
                assessment_id=a.id, title=a.title, type=a.type,
                adaptive_enabled=a.adaptive_enabled, submissions=0, avg_score=0.0,
            ))
            continue
        avg = sum(r.score for r in results) / len(results)
        per_concept: dict[str, list[float]] = {}
        labels: dict[str, str] = {}
        for r in results:
            for item in (r.item_scores or []):
                k, mx = item.get("concept_key"), item.get("max") or 0
                if k and mx > 0:
                    per_concept.setdefault(k, []).append(item.get("earned", 0) / mx)
            for crit in (r.rubric_criteria or []):
                k, mx = crit.get("concept_key"), crit.get("max_points") or 0
                if k and mx > 0:
                    per_concept.setdefault(k, []).append(crit.get("points", 0) / mx)
        for c in db.scalars(select(Concept).where(Concept.course_id == course_id)).all():
            labels[c.key] = c.name
        stats = [
            ConceptStat(concept_key=k, concept_name=labels.get(k, k),
                        avg=round(sum(v) / len(v), 3), n=len(v))
            for k, v in sorted(per_concept.items(), key=lambda kv: sum(kv[1]) / len(kv[1]))
        ]
        samples = [r.rubric_feedback for r in results if r.rubric_feedback][:3]
        out.append(AssessmentBreakdown(
            assessment_id=a.id, title=a.title, type=a.type,
            adaptive_enabled=a.adaptive_enabled, submissions=len(results),
            avg_score=round(avg, 3), concept_stats=stats, sample_rubric_feedback=samples,
        ))
    return out


@router.get("/courses/{course_id}/remediation", response_model=list[ModuleWithStudent])
def course_remediation(
    course_id: int, status: RemediationStatus | None = None,
    db: Session = Depends(get_db), user: User = Depends(require_instructor),
) -> list[ModuleWithStudent]:
    """Every remediation module in the course with its activities and student responses."""
    require_course_instructor(db, course_id, user)
    concept_names = {
        c.id: c.name
        for c in db.scalars(select(Concept).where(Concept.course_id == course_id)).all()
    }
    stmt = (
        select(RemediationModule)
        .where(RemediationModule.course_id == course_id)
        .options(
            selectinload(RemediationModule.activities).selectinload(RemediationActivity.responses),
            selectinload(RemediationModule.messages),
            selectinload(RemediationModule.student),
        )
        .order_by(RemediationModule.created_at.desc())
    )
    if status:
        stmt = stmt.where(RemediationModule.status == status)
    modules = db.scalars(stmt).all()
    return [
        ModuleWithStudent(
            id=m.id, student_id=m.student_id,
            student_name=m.student.full_name if m.student else str(m.student_id),
            concept_name=concept_names.get(m.concept_id), title=m.title, status=m.status,
            strategy=m.strategy.value, rationale=m.rationale, grounded_on=m.grounded_on,
            created_at=m.created_at,
            activities=[
                ActivityWithResponses(
                    id=a.id, sequence=a.sequence, activity_type=a.activity_type.value,
                    prompt=a.prompt,
                    responses=[
                        ResponseDetail(
                            id=resp.id, response_text=resp.response_text,
                            is_correct=resp.is_correct,
                            resolves_misconception=resp.resolves_misconception,
                            feedback=resp.feedback,
                        )
                        for resp in a.responses
                    ],
                )
                for a in m.activities
            ],
            transcript=[
                TranscriptTurn(role=t.role, content=t.content) for t in m.messages
            ],
        )
        for m in modules
    ]


@router.get("/courses/{course_id}/export.csv")
def export_csv(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(require_instructor)
) -> StreamingResponse:
    """Download per-student concept mastery + remediation status as CSV."""
    course = require_course_instructor(db, course_id, user)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "student_name", "email", "concept", "mastery_score", "status",
        "evidence_count", "open_modules", "completed_modules",
    ])
    students = db.scalars(
        select(User).join(Enrollment, Enrollment.user_id == User.id)
        .where(Enrollment.course_id == course_id, Enrollment.role == UserRole.student)
        .order_by(User.full_name)
    ).all()
    concepts = {
        c.id: c
        for c in db.scalars(select(Concept).where(Concept.course_id == course_id)).all()
    }
    for s in students:
        open_n = db.scalar(select(func.count(RemediationModule.id)).where(
            RemediationModule.student_id == s.id, RemediationModule.course_id == course_id,
            RemediationModule.status.in_(
                [RemediationStatus.pending, RemediationStatus.in_progress]),
        )) or 0
        done_n = db.scalar(select(func.count(RemediationModule.id)).where(
            RemediationModule.student_id == s.id, RemediationModule.course_id == course_id,
            RemediationModule.status == RemediationStatus.completed,
        )) or 0
        masteries = db.scalars(select(ConceptMastery).where(
            ConceptMastery.student_id == s.id,
            ConceptMastery.concept_id.in_(list(concepts) or [-1]),
        )).all()
        if not masteries:
            writer.writerow([s.full_name, s.email, "", "", "", 0, open_n, done_n])
        for m in masteries:
            c = concepts.get(m.concept_id)
            writer.writerow([
                s.full_name, s.email, c.name if c else m.concept_id,
                m.mastery_score, m.status.value, m.evidence_count, open_n, done_n,
            ])
    buf.seek(0)
    fname = f"{course.code.replace(' ', '_')}_analytics.csv"
    return StreamingResponse(
        iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
