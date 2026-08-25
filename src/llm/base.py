"""Base provider abstractions for LLM calls (R1 / EXT-08)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderResult:
    """Result of a single completion call, with observability metadata.

    ``error`` is set when the call ultimately failed after retries; ``raw`` is
    ``None`` in that case. ``retry_count`` records how many retries were used.
    """

    raw: str | None = None
    reasoning: str | None = None
    latency_ms: float | None = None
    retry_count: int = 0
    error: str | None = None
    model: str = ""
    usage: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.error is None and self.raw is not None

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "reasoning": self.reasoning,
            "latency_ms": self.latency_ms,
            "retry_count": self.retry_count,
            "error": self.error,
            "model": self.model,
            "usage": self.usage,
        }


class BaseLLMProvider(ABC):
    """Abstract provider contract: complete(messages, **gen_cfg) -> ProviderResult."""

    name: str = "base"

    @abstractmethod
    def complete(self, messages: list[dict[str, str]], **gen_cfg: Any) -> ProviderResult:
        """Run a chat completion and return a structured result."""
        raise NotImplementedError
