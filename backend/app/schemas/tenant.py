from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMModel


class TenantOut(ORMModel):
    id: int
    name: str
    slug: str
    ai_provider: str | None = None
    ai_model: str | None = None
    ai_endpoint: str | None = None
    ai_deployment: str | None = None
    external_ai_allowed: bool = True
    pii_minimization: bool = True
    # Never expose the key — only whether one is set.
    ai_key_set: bool = False
    # Licensing snapshot (read-only here; managed by the platform operator).
    subscription_status: str = "trial"
    plan: str = "pilot"
    seat_limit: int | None = None
    license_expires_at: datetime | None = None


class TenantLicenseRow(BaseModel):
    """One institution's license, for the platform operator's license console."""

    id: int
    name: str
    slug: str
    subscription_status: str
    plan: str
    seat_limit: int | None = None
    seats_used: int = 0
    license_expires_at: datetime | None = None


class TenantLicenseUpdate(BaseModel):
    subscription_status: str | None = None   # active|trial|expired|suspended|canceled
    plan: str | None = None                  # free|pilot|standard|enterprise
    seat_limit: int | None = None            # null = unlimited
    license_expires_at: datetime | None = None


class TenantAiUpdate(BaseModel):
    name: str | None = None
    ai_provider: str | None = None        # anthropic|openai|azure_openai|mock|"" (clear)
    ai_model: str | None = None
    ai_endpoint: str | None = None
    ai_deployment: str | None = None
    ai_api_key: str | None = None         # write-only; "" clears it
    external_ai_allowed: bool | None = None
    pii_minimization: bool | None = None
