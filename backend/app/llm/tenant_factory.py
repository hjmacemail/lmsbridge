"""Resolve the LLM provider for a given institution (tenant), honoring its BYO-AI
configuration and privacy policy. Falls back to the platform default when a tenant has
no AI configuration of its own.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crypto import decrypt_secret
from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.llm.factory import get_llm_provider
from app.llm.guard import GuardedProvider
from app.llm.providers.mock import MockProvider
from app.models.course import Course, Enrollment
from app.models.tenant import Tenant
from app.models.user import User

logger = get_logger("llm.tenant")


def _course_names(db: Session, course_id: int) -> list[str]:
    """Names of everyone in a course (students + instructor) so the privacy guard can scrub
    them from anything sent to the LLM — e.g. a student's name inside their own essay/code
    submission. Returns full names plus their individual tokens (len >= 4) to catch partial
    mentions, while avoiding over-redacting very short tokens."""
    names: set[str] = set()
    rows = db.execute(
        select(User.full_name).join(Enrollment, Enrollment.user_id == User.id)
        .where(Enrollment.course_id == course_id)
    ).scalars().all()
    course = db.get(Course, course_id)
    if course and course.owner_id:
        owner = db.get(User, course.owner_id)
        if owner and owner.full_name:
            rows = [*rows, owner.full_name]
    out: set[str] = set()
    for full in rows:
        full = (full or "").strip()
        if len(full) >= 3:
            out.add(full)
        for tok in full.split():
            if len(tok) >= 4:
                out.add(tok)
    return list(names | out)


def _provider_from_tenant(tenant: Tenant) -> LLMProvider | None:
    """Build a provider from a tenant's own AI config, or None if not configured."""
    provider = (tenant.ai_provider or "").lower()
    if not provider or provider == "mock":
        return MockProvider(tenant.ai_model or settings.llm_model) if provider == "mock" else None
    common = dict(max_tokens=settings.llm_max_tokens, temperature=settings.llm_temperature)
    key = decrypt_secret(tenant.ai_api_key_encrypted)
    model = tenant.ai_model or settings.llm_model
    try:
        if provider == "anthropic" and key:
            from app.llm.providers.anthropic_provider import AnthropicProvider
            return AnthropicProvider(model, key, **common)
        if provider == "openai" and key:
            from app.llm.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(model, key, **common)
        if provider == "azure_openai" and key and tenant.ai_endpoint:
            from app.llm.providers.openai_provider import AzureOpenAIProvider
            return AzureOpenAIProvider(
                tenant.ai_deployment or model, key, tenant.ai_endpoint, **common)
    except Exception as e:  # noqa: BLE001
        logger.error("Tenant %s AI config invalid (%s); using platform default.", tenant.id, e)
    return None


def resolve_provider(db: Session, *, course_id: int | None = None,
                     tenant: Tenant | None = None) -> LLMProvider:
    """Return a privacy-guarded provider for the tenant owning this course."""
    if tenant is None and course_id is not None:
        course = db.get(Course, course_id)
        if course and course.tenant_id:
            tenant = db.get(Tenant, course.tenant_id)

    inner = (_provider_from_tenant(tenant) if tenant else None) or get_llm_provider()
    pii = tenant.pii_minimization if tenant else True
    # Scrub course members' names from outgoing content (only needed when redaction is on).
    names = _course_names(db, course_id) if (pii and course_id is not None) else []
    return GuardedProvider(
        inner,
        fallback=MockProvider(settings.llm_model),
        pii_minimization=pii,
        external_allowed=(tenant.external_ai_allowed if tenant else True),
        redact_names=names,
    )


def tenant_for_course(db: Session, course_id: int) -> Tenant | None:
    course = db.get(Course, course_id)
    if course and course.tenant_id:
        return db.scalar(select(Tenant).where(Tenant.id == course.tenant_id))
    return None
