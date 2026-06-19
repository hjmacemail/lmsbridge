from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin
from app.db.session import get_db
from app.models.lead import Lead
from app.models.user import User
from app.schemas.lead import LeadCreate, LeadOut

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadOut, status_code=201)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> Lead:
    """Public endpoint: capture a demo/purchase/contact request from the marketing site."""
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


@router.get("", response_model=list[LeadOut])
def list_leads(
    db: Session = Depends(get_db), _: User = Depends(require_platform_admin)
) -> list[Lead]:
    """Platform-admin only: review captured sales leads."""
    return list(db.scalars(select(Lead).order_by(Lead.created_at.desc())).all())
