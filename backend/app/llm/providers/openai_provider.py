"""OpenAI and Azure OpenAI providers (optional: `pip install lms-bridge[openai]`)."""
from __future__ import annotations

from app.llm.base import LLMMessage, LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, model: str, api_key: str, **kw) -> None:
        super().__init__(model, **kw)
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "openai package not installed. Run: pip install 'lms-bridge[openai]'"
            ) from e
        self._client = OpenAI(api_key=api_key)

    def complete(self, messages: list[LLMMessage], *, json_mode: bool = False) -> LLMResponse:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self._client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        return LLMResponse(text=text, model=self.model, provider=self.name)


class AzureOpenAIProvider(LLMProvider):
    """Azure-hosted OpenAI — common for university-approved/compliant deployments."""

    name = "azure_openai"

    def __init__(self, deployment: str, api_key: str, endpoint: str, **kw) -> None:
        super().__init__(deployment, **kw)
        try:
            from openai import AzureOpenAI
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "openai package not installed. Run: pip install 'lms-bridge[openai]'"
            ) from e
        self._client = AzureOpenAI(
            api_key=api_key, azure_endpoint=endpoint, api_version="2024-06-01"
        )

    def complete(self, messages: list[LLMMessage], *, json_mode: bool = False) -> LLMResponse:
        kwargs: dict = {
            "model": self.model,  # = deployment name
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        resp = self._client.chat.completions.create(**kwargs)
        text = resp.choices[0].message.content or ""
        return LLMResponse(text=text, model=self.model, provider=self.name)
