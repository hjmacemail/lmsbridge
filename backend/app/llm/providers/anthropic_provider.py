"""Anthropic Claude provider (optional dependency: `pip install lms-bridge[anthropic]`)."""
from __future__ import annotations

from app.llm.base import LLMMessage, LLMProvider, LLMResponse


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, model: str, api_key: str, **kw) -> None:
        super().__init__(model, **kw)
        try:
            import anthropic
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "anthropic package not installed. Run: pip install 'lms-bridge[anthropic]'"
            ) from e
        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(self, messages: list[LLMMessage], *, json_mode: bool = False) -> LLMResponse:
        system = "\n".join(m.content for m in messages if m.role == "system")
        chat = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role in ("user", "assistant")
        ]
        if json_mode:
            system += "\n\nRespond with a single valid JSON object and nothing else."
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system or None,
            messages=chat,
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        return LLMResponse(text=text, model=self.model, provider=self.name)
