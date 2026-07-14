from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """An institution. Holds its own (optional) AI configuration and privacy policy,
    so each institution can run inference through its OWN model/key and decide what may
    leave its boundary. When no AI config is set, the platform default is used.
    """

    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    lti_registration_id: Mapped[int | None] = mapped_column(
        ForeignKey("lti_registrations.id", ondelete="SET NULL")
    )

    # --- Bring-your-own AI (admin-configured) ---
    # anthropic | openai | azure_openai | mock
    ai_provider: Mapped[str | None] = mapped_column(String(32))
    ai_model: Mapped[str | None] = mapped_column(String(128))
    ai_endpoint: Mapped[str | None] = mapped_column(String(512))  # Azure endpoint
    ai_deployment: Mapped[str | None] = mapped_column(String(128))
    ai_api_key_encrypted: Mapped[str | None] = mapped_column(String(1024))

    # --- Privacy policy ---
    # When False, live student content is never sent to an external commercial API
    # (the engine falls back to a local/self-hosted model or the safe mock).
    external_ai_allowed: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true()
    )
    # When True, identifiers are redacted from anything sent to the model.
    pii_minimization: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true()
    )
    # Institution-wide default UI/AI language (base code, e.g. "es"). Used when the LMS launch
    # doesn't carry a locale. Null = follow the LMS/user, then browser, then English.
    default_locale: Mapped[str | None] = mapped_column(String(8))

    # --- Licensing / subscription (enforced at LTI launch) ---
    # active | trial | expired | suspended | canceled
    subscription_status: Mapped[str] = mapped_column(
        String(32), default="trial", server_default="trial"
    )
    # free | pilot | standard | enterprise (informational tier label)
    plan: Mapped[str] = mapped_column(String(32), default="pilot", server_default="pilot")
    # Max distinct students that may launch; NULL = unlimited.
    seat_limit: Mapped[int | None] = mapped_column(Integer)
    # Hard expiry; NULL = no expiry. Past this instant, launches are blocked.
    license_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
