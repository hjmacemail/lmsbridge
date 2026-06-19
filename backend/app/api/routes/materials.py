from __future__ import annotations

import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_instructor
from app.db.session import get_db
from app.models.concept import Concept
from app.models.course import Course
from app.models.material import CourseMaterial
from app.models.user import User
from app.schemas.material import MaterialDetail, MaterialOut
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
    course_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> list[MaterialOut]:
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
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
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


@router.get("/{material_id}/download")
def download_material(
    material_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
) -> StreamingResponse:
    m = db.get(CourseMaterial, material_id)
    if not m or m.content is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return StreamingResponse(
        io.BytesIO(m.content),
        media_type=m.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{m.filename}"'},
    )


@router.delete("/{material_id}", status_code=204)
def delete_material(
    material_id: int, db: Session = Depends(get_db), _: User = Depends(require_instructor)
) -> None:
    m = db.get(CourseMaterial, material_id)
    if not m:
        raise HTTPException(status_code=404, detail="Material not found")
    db.delete(m)
    db.commit()
