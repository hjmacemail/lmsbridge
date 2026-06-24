"""Application configuration via environment variables / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # Application
    app_env: str = "development"
    app_name: str = "LMS Bridge"
    log_level: str = "INFO"
    api_port: int = 8000

    # Deployment model:
    #  - "community" (default): a single self-hosted institution. No license gate (launches
    #    are never blocked), no sales/leads surfaces, and the institution admin manages
    #    everything (including their own LMS registration). This is the open-source default.
    #  - "hosted": multi-tenant SaaS run by an operator — enables the platform-operator role,
    #    lead capture, and per-tenant license/subscription enforcement.
    deployment_mode: str = "community"

    # Public "try the demo" affordance: enables POST /auth/demo-login, which signs you in as
    # the seeded demo student/instructor (no password) so the marketing site's simulated-LMS
    # demo works for anyone. Set false on a real institutional deployment.
    demo_login_enabled: bool = True

    # Security
    secret_key: str = "dev-secret-change-me"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    # Stored as a raw comma-separated string to avoid pydantic-settings JSON-decoding
    # env vars typed as lists. Use `cors_origins` (the property) everywhere in code.
    cors_origins_raw: str = Field(
        default="http://localhost:5173", validation_alias="CORS_ORIGINS"
    )

    # Database
    database_url: str = "sqlite+pysqlite:///./lmsbridge.db"

    @field_validator("database_url", mode="after")
    @classmethod
    def _normalize_db_url(cls, v: str) -> str:
        # Managed hosts (Render/Railway/Fly/Heroku) hand out `postgres://` or
        # `postgresql://` URLs, which SQLAlchemy maps to the psycopg2 driver. We ship
        # psycopg 3, so rewrite the scheme to `postgresql+psycopg://`.
        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    # LLM
    llm_provider: str = "mock"
    llm_model: str = "claude-3-5-sonnet-latest"
    llm_max_tokens: int = 1200
    llm_temperature: float = 0.3
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_endpoint: str | None = None
    azure_openai_deployment: str | None = None

    # Brightspace
    brightspace_adapter: str = "mock"
    brightspace_base_url: str | None = None
    brightspace_app_id: str | None = None
    brightspace_app_key: str | None = None
    brightspace_user_id: str | None = None
    brightspace_user_key: str | None = None

    # Remediation engine
    remediation_trigger_threshold: float = 0.7
    mastery_threshold: float = 0.85

    # LTI 1.3 — public base URLs used to build launch/redirect targets.
    tool_base_url: str = "http://localhost:8000"        # this backend's public URL
    frontend_base_url: str = "http://localhost:8080"    # the SPA's public URL

    # Platform-operator bootstrap. If set, the backend ensures this account exists as a
    # platform admin on every startup (idempotent) — so operators can be provisioned on
    # hosts without shell access (e.g. Render free tier) by setting two env vars + redeploy.
    platform_admin_email: str | None = None
    platform_admin_password: str | None = None

    # Licensing.
    #  - SaaS mode (default): per-tenant subscription_status is enforced at LTI launch.
    #  - Self-hosted mode: set LICENSE_PUBLIC_KEY (vendor's PEM) to require a signed
    #    LICENSE_KEY token, validated offline at startup. Without a valid token the
    #    install is "unlicensed" and launches are blocked.
    license_public_key: str | None = None     # vendor public key (PEM), self-hosted only
    license_key: str | None = None            # the signed license token (JWT)
    license_contact_email: str = "sales@lmsbridge.app"  # shown on the blocked screen
    # Bypass all license gating (local dev / demos). Never set true in production.
    license_enforcement_disabled: bool = False

    # Optional SMTP for email notifications (e.g. Sage announcements). If smtp_host is unset,
    # email is a no-op — the app works fine without it.
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None       # e.g. "Sage <noreply@your-school.edu>"
    smtp_starttls: bool = True
    smtp_ssl: bool = False             # use SMTPS (implicit TLS) instead of STARTTLS

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
