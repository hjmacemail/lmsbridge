from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_instructor
from app.core.crypto import decrypt_secret
from app.db.session import get_db
from app.integrations import lms_files
from app.integrations.lms_common import is_text_file
from app.models.concept import Concept
from app.models.course import Course
from app.models.material import CourseMaterial
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.material import LmsImportRequest, MaterialDetail, MaterialOut
from app.services.course_access import require_course_instructor, require_course_member
from app.services.material_service import MAX_UPLOAD_BYTES, create_material

router = APIRouter(prefix="/materials", tags=["materials"])


def _to_out(m: CourseMaterial) -> MaterialOut:
    return MaterialOut(
        id=m.id, course_id=m.course_id, concept_id=m.concept_id, title=m.title,
        filename=m.filename, content_type=m.content_type, size_bytes=m.size_bytes,
        has_text=bool(m.extracted_text), created_at=m.created_at,
    )


@router.get("", response_model=list[MaterialOut])
def list_materials(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[MaterialOut]:
    require_course_member(db, course_id, user)
    rows = db.scalars(
        select(CourseMaterial)
        .where(CourseMaterial.course_id == course_id)
        .order_by(CourseMaterial.created_at.desc())
    ).all()
    return [_to_out(m) for m in rows]


@router.post("", response_model=MaterialDetail, status_code=201)
async def upload_material(
    course_id: int = Form(...),
    title: str = Form(""),
    concept_id: int | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_instructor),
) -> MaterialDetail:
    require_course_instructor(db, course_id, user)
    if concept_id is not None and not db.get(Concept, concept_id):
        raise HTTPException(status_code=404, detail="Concept not found")

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit")
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    material = create_material(
        db, course_id=course_id, title=title or file.filename or "Untitled",
        filename=file.filename or "upload", content_type=file.content_type or "",
        data=data, concept_id=concept_id, uploaded_by=user.id,
    )
    db.commit()
    db.refresh(material)
    out = _to_out(material)
    preview = (material.extracted_text or "")[:600] or None
    return MaterialDetail(**out.model_dump(), text_preview=preview)


def _run_import(db, course, provider_name, base_url, token, lms_course_id, uploaded_by) -> dict:
    """Shared core: list a course's files via the LMS API and import the document-type ones."""
    try:
        provider = lms_files.get_provider(provider_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        listing = provider.list_course_files(base_url, token, lms_course_id)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Could not list LMS files: {e}") from e

    imported = skipped = 0
    for f in listing:
        name = f.get("name") or "file"
        ext_ref = f"{provider_name}::{f.get('id')}"
        # Brightspace topic titles can lack an extension; still import (extraction is best-effort).
        if provider_name != "brightspace" and not is_text_file(name):
            skipped += 1
            continue
        exists = db.scalar(
            select(CourseMaterial).where(
                CourseMaterial.course_id == course.id,
                CourseMaterial.filename.in_([name, ext_ref]),
            )
        )
        if exists:
            skipped += 1
            continue
        url = f.get("download_url")
        if not url:
            skipped += 1
            continue
        try:
            data = provider.download_file(url, token, max_bytes=MAX_UPLOAD_BYTES)
        except Exception:  # noqa: BLE001 — one bad file shouldn't abort the whole import
            skipped += 1
            continue
        create_material(
            db, course_id=course.id, title=name, filename=name,
            content_type=f.get("content_type") or "application/octet-stream",
            data=data, concept_id=None, uploaded_by=uploaded_by,
        )
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "total": len(listing)}


def _tenant_lms(db: Session, course: Course) -> tuple[Tenant | None, bool]:
    tenant = db.get(Tenant, course.tenant_id) if course.tenant_id else None
    connected = bool(
        tenant and tenant.lms_provider and tenant.lms_base_url and tenant.lms_api_key_encrypted
    )
    return tenant, connected


@router.get("/import/lms/status")
def lms_import_status(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(require_instructor)
) -> dict:
    """Whether this course can be imported with one click (institution LMS connected + course
    reference known from the LTI launch) — so the instructor never has to enter a token."""
    course = require_course_instructor(db, course_id, user)
    tenant, connected = _tenant_lms(db, course)
    return {
        "connected": connected,
        "provider": tenant.lms_provider if connected else None,
        "has_course_ref": bool(course.lms_course_ref),
        "can_import": connected and bool(course.lms_course_ref),
    }


@router.post("/import/lms/auto")
def import_from_lms_auto(
    course_id: int, db: Session = Depends(get_db), user: User = Depends(require_instructor)
) -> dict:
    """One-click import using the institution's admin-configured LMS connection and the course's
    launch reference. The instructor supplies NO token, URL, or course id."""
    course = require_course_instructor(db, course_id, user)
    tenant, connected = _tenant_lms(db, course)
    if not connected:
        raise HTTPException(status_code=409,
            detail="Your institution hasn't connected an LMS yet. Ask your admin to set it up in Settings.")
    if not course.lms_course_ref:
        raise HTTPException(status_code=409,
            detail="This course has no LMS reference yet — open LMS Bridge from inside the course first.")
    token = decrypt_secret(tenant.lms_api_key_encrypted)
    return _run_import(db, course, tenant.lms_provider, tenant.lms_base_url,
                       token, course.lms_course_ref, user.id)


@router.post("/import/lms")
def import_from_lms(
    payload: LmsImportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_instructor),
) -> dict:
    """Manual import (advanced/fallback): the caller supplies the LMS URL, token, and course id.
    Prefer the one-click /import/lms/auto flow so instructors never handle tokens."""
    course = require_course_instructor(db, payload.course_id, user)
    return _run_import(db, course, payload.provider, payload.base_url,
                       payload.access_token, payload.lms_course_id, user.id)


@router.get("/{material_id}/download")
def download_material(
    material_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> StreamingResponse:
    m = db.get(CourseMaterial, material_id)
    if not m or m.content is None:
        raise HTTPException(status_code=404, detail="Material not found")
    require_course_member(db, m.course_id, user)
    return StreamingResponse(
        io.BytesIO(m.content),
        media_type=m.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{m.filename}"'},
    )


@router.delete("/{material_id}", status_code=204)
def delete_material(
    material_id: int, db: Session = Depends(get_db), user: User = Depends(require_instructor)
) -> None:
    m = db.get(CourseMaterial, material_id)
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")
    require_course_instructor(db, m.course_id, user)
    db.delete(m)
    db.commit()
