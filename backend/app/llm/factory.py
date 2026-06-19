"""Factory that builds the configured LLM provider."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.llm.providers.mock import MockProvider

logger = get_logger("llm")


@lru_cache
def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider.lower()
    common = dict(max_tokens=settings.llm_max_tokens, temperature=settings.llm_temperature)

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            logger.warning("LLM_PROVIDER=anthropic but no API key set; falling back to mock.")
            return MockProvider(settings.llm_model, **common)
        from app.llm.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(settings.llm_model, settings.anthropic_api_key, **common)

    if provider == "openai":
        if not settings.openai_api_key:
            logger.warning("LLM_PROVIDER=openai but no API key set; falling back to mock.")
            return MockProvider(settings.llm_model, **common)
        from app.llm.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(settings.llm_model, settings.openai_api_key, **common)

    if provider == "azure_openai":
        if not (settings.azure_openai_api_key and settings.azure_openai_endpoint):
            logger.warning("LLM_PROVIDER=azure_openai misconfigured; falling back to mock.")
            return MockProvider(settings.llm_model, **common)
        from app.llm.providers.openai_provider import AzureOpenAIProvider
        return AzureOpenAIProvider(
            settings.azure_openai_deployment or settings.llm_model,
            settings.azure_openai_api_key,
            settings.azure_openai_endpoint,
            **common,
        )

    return MockProvider(settings.llm_model, **common)
