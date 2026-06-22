from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_instructor
from app.db.session import get_db
from app.integrations import lms_files
from app.integrations.lms_common import is_text_file
from app.models.concept import Concept
from app.models.material import CourseMaterial
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


@router.post("/import/lms")
def import_from_lms(
    payload: LmsImportRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_instructor),
) -> dict:
    """Import an LMS course's files as CourseMaterial via that LMS's API.

    Supports Canvas (REST), Moodle (web services), and Brightspace (Valence). Document-type
    files (PDF/DOCX/PPTX/TXT/MD/HTML/CSV/RTF) are downloaded and text-extracted for AI grounding;
    other types and already-imported files are skipped. The token is used transiently, not stored.
    """
    course = require_course_instructor(db, payload.course_id, user)
    try:
        provider = lms_files.get_provider(payload.provider)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        listing = provider.list_course_files(
            payload.base_url, payload.access_token, payload.lms_course_id
        )
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Could not list LMS files: {e}") from e

    imported = skipped = 0
    for f in listing:
        name = f.get("name") or "file"
        ext_ref = f"{payload.provider}::{f.get('id')}"
        # Brightspace topic titles can lack an extension; still import (extraction is best-effort).
        if payload.provider != "brightspace" and not is_text_file(name):
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
            data = provider.download_file(url, payload.access_token, max_bytes=MAX_UPLOAD_BYTES)
        except Exception:  # noqa: BLE001 — one bad file shouldn't abort the whole import
            skipped += 1
            continue
        create_material(
            db, course_id=course.id, title=name, filename=name,
            content_type=f.get("content_type") or "application/octet-stream",
            data=data, concept_id=None, uploaded_by=user.id,
        )
        imported += 1

    db.commit()
    return {"imported": imported, "skipped": skipped, "total": len(listing)}


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
