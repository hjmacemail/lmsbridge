"""Ingest AGS gradebook results into the adaptive pipeline.

AGS exposes line-item scores (not per-question detail). The instructor maps each LMS
line item to a concept key when onboarding the course; this turns each student result
into a concept-level signal the mastery model can use. For full distractor-level MCQ
diagnosis, deliver the formative quiz through LMS Bridge itself.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.lti import services
from app.lti.launch import LtiLaunch
from app.models.assessment import Assessment
from app.models.enums import AssessmentType, UserRole
from app.models.lti import LtiRegistration
from app.models.user import User
from app.services.ingestion_service import ingest_result


def sync_course_from_ags(
    db: Session, *, course_id: int, reg: LtiRegistration, ags_endpoint: dict,
    lineitem_to_concept: dict[str, str], auto_remediate: bool = True,
) -> dict:
    """Pull AGS line items + results and run them through the ingestion pipeline."""
    lineitems_url = ags_endpoint.get("lineitems")
    if not lineitems_url:
        return {"ingested": 0, "modules": 0, "note": "no lineitems endpoint in AGS claim"}

    lineitems = services.ags_get_lineitems(db, reg, lineitems_url)
    ingested = modules = 0
    for li in lineitems:
        li_url = li.get("id")
        concept_key = lineitem_to_concept.get(li.get("label") or li.get("id", ""))
        if not (li_url and concept_key):
            continue
        assessment = _ensure_assessment(db, course_id, li)
        for result in services.ags_get_results(db, reg, li_url):
            user = db.scalar(
                select(User).where(
                    User.external_id == f"lti::{reg.issuer}::{result.get('userId')}"
                )
            )
            if not user:
                continue
            mx = result.get("resultMaximum") or li.get("scoreMaximum") or 1
            score = (result.get("resultScore") or 0) / mx if mx else 0
            _, mods = ingest_result(
                db, assessment=assessment, student=user, score=score,
                item_scores=[{"concept_key": concept_key,
                              "earned": result.get("resultScore") or 0, "max": mx}],
                rubric_feedback=result.get("comment"),
                auto_remediate=auto_remediate,
            )
            ingested += 1
            modules += len(mods)
    return {"ingested": ingested, "modules": modules}


def _ensure_assessment(db: Session, course_id: int, lineitem: dict) -> Assessment:
    ext = f"lti::{lineitem.get('id')}"
    a = db.scalar(select(Assessment).where(Assessment.brightspace_assessment_id == ext))
    if not a:
        a = Assessment(
            course_id=course_id, brightspace_assessment_id=ext,
            title=lineitem.get("label") or "LMS Assessment",
            type=AssessmentType.assignment,
            max_score=lineitem.get("scoreMaximum") or 100,
            available_at=datetime.now(timezone.utc),
        )
        db.add(a)
        db.flush()
    return a


def membership_roster(db: Session, reg: LtiRegistration, launch: LtiLaunch) -> list[dict]:
    """Convenience: NRPS roster for the launch context."""
    nrps = launch.nrps or {}
    url = nrps.get("context_memberships_url")
    members = services.nrps_get_members(db, reg, url) if url else []
    return [
        {"user_id": m.get("user_id"), "name": m.get("name"), "email": m.get("email"),
         "roles": m.get("roles", []),
         "role": "instructor" if any("Instructor" in r for r in m.get("roles", []))
                 else UserRole.student.value}
        for m in members
    ]
