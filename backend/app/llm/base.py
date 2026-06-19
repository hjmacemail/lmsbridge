"""Provider-agnostic LLM interface.

All providers implement the same `complete()` contract so the rest of the system
never depends on a specific vendor. Selection is driven by configuration, which
keeps student-data processing inside approved infrastructure (FERPA / governance).
"""
from __future__ import annotations

import abc
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str
    raw: dict | None = None


class LLMProvider(abc.ABC):
    """Abstract base every concrete provider must implement."""

    name: str = "base"

    def __init__(self, model: str, max_tokens: int = 1200, temperature: float = 0.3) -> None:
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    @abc.abstractmethod
    def complete(self, messages: list[LLMMessage], *, json_mode: bool = False) -> LLMResponse:
        """Return a completion for the given messages."""

    def __repr__(self) -> str:  # pragma: no cover
        return f"<{self.__class__.__name__} model={self.model}>"
