from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class LtiToolKey(Base, TimestampMixin):
    """The tool's RSA signing key (exposed via JWKS, used to sign client assertions)."""

    __tablename__ = "lti_tool_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    kid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    private_pem: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class LtiRegistration(Base, TimestampMixin):
    """A registered LMS platform (one per institution/LMS instance).

    Holds the OpenID Connect / OAuth2 endpoints the platform exposes, used to verify
    launches and to obtain access tokens for the LTI Advantage services.
    """

    __tablename__ = "lti_registrations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    issuer: Mapped[str] = mapped_column(String(512), index=True)          # platform iss
    client_id: Mapped[str] = mapped_column(String(255))            # our tool's client id
    auth_login_url: Mapped[str] = mapped_column(String(512))       # platform OIDC auth url
    auth_token_url: Mapped[str] = mapped_column(String(512))       # platform OAuth2 token url
    key_set_url: Mapped[str] = mapped_column(String(512))          # platform JWKS url
    audience: Mapped[str | None] = mapped_column(String(512))      # token audience override
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Trust the deployment_id from the first verified launch (used by dynamic registration).
    auto_register_deployments: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false()
    )

    deployments: Mapped[list[LtiDeployment]] = relationship(
        back_populates="registration", cascade="all, delete-orphan"
    )

    __table_args__ = (UniqueConstraint("issuer", "client_id", name="uq_lti_reg_iss_client"),)


class LtiDeployment(Base, TimestampMixin):
    __tablename__ = "lti_deployments"

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_id: Mapped[int] = mapped_column(
        ForeignKey("lti_registrations.id", ondelete="CASCADE")
    )
    deployment_id: Mapped[str] = mapped_column(String(255))
    label: Mapped[str | None] = mapped_column(String(255))

    registration: Mapped[LtiRegistration] = relationship(back_populates="deployments")

    __table_args__ = (
        UniqueConstraint("registration_id", "deployment_id", name="uq_lti_deployment"),
    )


class LtiNonce(Base):
    """Login state + nonce, created at OIDC login and consumed once at launch (anti-replay)."""

    __tablename__ = "lti_nonces"

    id: Mapped[int] = mapped_column(primary_key=True)
    state: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    nonce: Mapped[str] = mapped_column(String(128), index=True)
    registration_id: Mapped[int | None] = mapped_column(
        ForeignKey("lti_registrations.id", ondelete="CASCADE")
    )
    target_link_uri: Mapped[str | None] = mapped_column(String(1024))
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
