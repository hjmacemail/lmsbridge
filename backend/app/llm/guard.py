"""Privacy guard wrapping any LLM provider.

Two enforced policies, configured per institution (tenant):
  * PII minimization — redact identifiers from every message before it leaves the process.
  * External-AI policy — if the institution forbids sending live student content to an
    external commercial API, requests are routed to a safe local fallback instead of leaking.
"""
from __future__ import annotations

from dataclasses import replace

from app.core.logging import get_logger
from app.core.privacy import redact_pii
from app.llm.base import LLMMessage, LLMProvider, LLMResponse

logger = get_logger("llm.guard")

# Providers that call an external, vendor-controlled endpoint.
EXTERNAL_PROVIDERS = {"anthropic", "openai"}


class GuardedProvider(LLMProvider):
    """Decorates a provider with PII redaction and the external-AI policy."""

    name = "guarded"

    def __init__(
        self,
        inner: LLMProvider,
        *,
        fallback: LLMProvider,
        pii_minimization: bool = True,
        external_allowed: bool = True,
        redact_names: list[str] | None = None,
    ) -> None:
        super().__init__(inner.model, inner.max_tokens, inner.temperature)
        self._inner = inner
        self._fallback = fallback
        self._pii = pii_minimization
        self._external_allowed = external_allowed
        self._names = redact_names or []

    def _target(self) -> LLMProvider:
        if self._inner.name in EXTERNAL_PROVIDERS and not self._external_allowed:
            logger.warning(
                "External AI (%s) blocked by tenant policy; using local fallback (%s).",
                self._inner.name, self._fallback.name,
            )
            return self._fallback
        return self._inner

    def complete(self, messages: list[LLMMessage], *, json_mode: bool = False) -> LLMResponse:
        if self._pii:
            messages = [replace(m, content=redact_pii(m.content, self._names)) for m in messages]
        target = self._target()
        try:
            return target.complete(messages, json_mode=json_mode)
        except Exception as e:  # noqa: BLE001 — never 500 on a provider error; degrade gracefully.
            if target is self._fallback:
                raise
            logger.error(
                "LLM provider '%s' failed (%s); using local fallback. Check the API key, "
                "model id, and account credit.", target.name, e,
            )
            return self._fallback.complete(messages, json_mode=json_mode)
