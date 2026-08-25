"""Deterministic mock provider for tests and offline development.

Never makes a real network call. Returns a fixed sequence of responses (or a
default), making it suitable for parser/schema/evaluator unit tests that must
not consume real Hy3 API quota.
"""
from __future__ import annotations

from typing import Any

from src.llm.base import BaseLLMProvider, ProviderResult


class MockProvider(BaseLLMProvider):
    name = "mock"

    def __init__(
        self,
        responses: list[str] | None = None,
        *,
        default: str = "",
        reasoning: str | None = None,
    ) -> None:
        self._responses = list(responses) if responses else []
        self._default = default
        self._reasoning = reasoning
        self._call_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    def complete(self, messages: list[dict[str, str]], **gen_cfg: Any) -> ProviderResult:
        self._call_count += 1
        idx = self._call_count - 1
        raw = self._responses[idx] if idx < len(self._responses) else self._default
        return ProviderResult(
            raw=raw, reasoning=self._reasoning, latency_ms=0.0, retry_count=0, model="mock"
        )
