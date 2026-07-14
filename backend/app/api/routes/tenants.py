"""Admin-only institution (tenant) settings: bring-your-own AI + privacy policy.

The institution admin configures the model/key/endpoint and privacy controls here.
The API never returns the stored API key — only whether one is set.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_platform_admin, require_role
from app.core.crypto import encrypt_secret
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.tenant import (
    TenantAiUpdate,
    TenantLicenseRow,
    TenantLicenseUpdate,
    TenantOut,
)
from app.services import license_service

router = APIRouter(prefix="/tenants", tags=["tenants"])
require_admin = require_role(UserRole.admin)

_VALID_STATUS = {"active", "trial", "expired", "suspended", "canceled"}


def _to_out(t: Tenant) -> TenantOut:
    return TenantOut(
        id=t.id, name=t.name, slug=t.slug, ai_provider=t.ai_provider, ai_model=t.ai_model,
        ai_endpoint=t.ai_endpoint, ai_deployment=t.ai_deployment,
        external_ai_allowed=t.external_ai_allowed, pii_minimization=t.pii_minimization,
        default_locale=t.default_locale,
        ai_key_set=bool(t.ai_api_key_encrypted),
        subscription_status=t.subscription_status, plan=t.plan,
        seat_limit=t.seat_limit, license_expires_at=t.license_expires_at,
    )


def _resolve_tenant(db: Session, admin: User) -> Tenant:
    """The admin's own tenant, or the first/default tenant (single-institution deploys)."""
    if admin.tenant_id:
        t = db.get(Tenant, admin.tenant_id)
        if t:
            return t
    t = db.scalar(select(Tenant).order_by(Tenant.id))
    if not t:
        t = Tenant(name="Default Institution", slug="default")
        db.add(t)
        db.commit()
        db.refresh(t)
    return t


@router.get("/me", response_model=TenantOut)
def my_tenant(db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> TenantOut:
    return _to_out(_resolve_tenant(db, admin))


@router.get("/license/status")
def license_status(db: Session = Depends(get_db), admin: User = Depends(require_admin)) -> dict:
    """License state for the current admin's institution (mode + self-hosted + tenant snapshot)."""
    return license_service.license_summary(db, _resolve_tenant(db, admin))


@router.get("/licenses", response_model=list[TenantLicenseRow])
def list_licenses(
    db: Session = Depends(get_db), _: User = Depends(require_platform_admin)
) -> list[TenantLicenseRow]:
    """Every institution's license — platform operator only."""
    rows: list[TenantLicenseRow] = []
    for t in db.scalars(select(Tenant).order_by(Tenant.id)).all():
        rows.append(TenantLicenseRow(
            id=t.id, name=t.name, slug=t.slug,
            subscription_status=t.subscription_status, plan=t.plan,
            seat_limit=t.seat_limit, seats_used=license_service.count_students(db, t),
            license_expires_at=t.license_expires_at,
        ))
    return rows


@router.put("/{tenant_id}/license", response_model=TenantLicenseRow)
def update_license(
    tenant_id: int, payload: TenantLicenseUpdate,
    db: Session = Depends(get_db), _: User = Depends(require_platform_admin),
) -> TenantLicenseRow:
    """Set an institution's subscription/plan/seats/expiry — platform operator only."""
    t = db.get(Tenant, tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    data = payload.model_dump(exclude_unset=True)
    if "subscription_status" in data and data["subscription_status"] not in _VALID_STATUS:
        raise HTTPException(status_code=400, detail="Invalid subscription_status")
    for field, value in data.items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return TenantLicenseRow(
        id=t.id, name=t.name, slug=t.slug,
        subscription_status=t.subscription_status, plan=t.plan,
        seat_limit=t.seat_limit, seats_used=license_service.count_students(db, t),
        license_expires_at=t.license_expires_at,
    )


@router.put("/me/ai", response_model=TenantOut)
def update_ai(
    payload: TenantAiUpdate, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> TenantOut:
    t = _resolve_tenant(db, admin)
    data = payload.model_dump(exclude_unset=True)

    if "ai_api_key" in data:
        key = data.pop("ai_api_key")
        t.ai_api_key_encrypted = encrypt_secret(key) if key else None
    for field in ("name", "ai_provider", "ai_model", "ai_endpoint", "ai_deployment",
                  "external_ai_allowed", "pii_minimization", "default_locale"):
        if field in data:
            value = data[field]
            # Treat empty provider/model/locale strings as "clear".
            setattr(t, field, value if value != "" else None)

    if t.ai_provider and t.ai_provider not in ("anthropic", "openai", "azure_openai", "mock"):
        raise HTTPException(status_code=400, detail="Unsupported ai_provider")
    from app.core.i18n import SUPPORTED_LANGS
    if t.default_locale and t.default_locale not in SUPPORTED_LANGS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported default_locale; choose one of {', '.join(SUPPORTED_LANGS)}",
        )
    db.commit()
    db.refresh(t)
    return _to_out(t)
