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
            # NOTE: do NOT prefill the assistant turn with "{" — newer Claude models (Sonnet 4.x)
            # reject assistant-message prefill ("conversation must end with a user message").
            # A firm instruction + the tolerant extract_json parser is enough for reliable JSON.
            system += (
                "\n\nRespond with ONLY a single valid JSON object and nothing else — no prose, "
                "no code fences. This applies on every turn, even for short or unclear messages."
            )
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system or None,
            messages=chat,
        )
        text = "".join(block.text for block in resp.content if block.type == "text")
        return LLMResponse(text=text, model=self.model, provider=self.name)
