"""Secure-by-default checks: production must not run with the dev secret or expose the
password-less demo sign-in into a real (self-hosted) deployment."""
from __future__ import annotations

from app.core.config import DEFAULT_SECRET_KEY, Settings


def _s(**kw) -> Settings:
    return Settings(_env_file=None, **kw)


def test_default_secret_blocks_only_in_production():
    assert _s(app_env="production", secret_key=DEFAULT_SECRET_KEY).security_errors()
    assert _s(app_env="production", secret_key="a-strong-unique-key").security_errors() == []
    # Dev keeps the convenient default — no error.
    assert _s(app_env="development", secret_key=DEFAULT_SECRET_KEY).security_errors() == []


def test_demo_login_active_rules():
    # Non-production: available when enabled.
    assert _s(app_env="development").demo_login_active is True
    assert _s(app_env="development", demo_login_enabled=False).demo_login_active is False
    # Production self-hosted institution: never active (would be a password-less real login).
    assert _s(app_env="production", deployment_mode="community",
              secret_key="k").demo_login_active is False
    # Production multi-tenant hosted demo: honored when enabled.
    assert _s(app_env="production", deployment_mode="hosted",
              secret_key="k").demo_login_active is True
    assert _s(app_env="production", deployment_mode="hosted", secret_key="k",
              demo_login_enabled=False).demo_login_active is False
