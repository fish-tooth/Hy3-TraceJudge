"""Parsing raw LLM output into a validated ``Solution`` (R4).

A parse failure is recorded as an explicit ``FAILURE`` status and is never
silently dropped, so it can be surfaced in failure accounting.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from src.solver.schema import Solution


@dataclass
class ParseResult:
    status: str  # "SUCCESS" or "FAILURE"
    solution: Solution | None = None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == "SUCCESS" and self.solution is not None


def _extract_json(text: str) -> Any:
    text = text.strip()
    # Strip markdown code fences if the model wrapped the JSON in ```json ... ```.
    if text.startswith("```"):
        lines = [ln for ln in text.splitlines() if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fall back to locating the first balanced JSON object if prose surrounds it.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError("no valid JSON object found in response")


def parse_solution(raw: str) -> ParseResult:
    if not raw or not raw.strip():
        return ParseResult(status="FAILURE", error="empty response")

    try:
        data = _extract_json(raw)
    except (ValueError, json.JSONDecodeError) as exc:
        return ParseResult(status="FAILURE", error=f"JSON decode failed: {exc}")

    if not isinstance(data, dict):
        return ParseResult(status="FAILURE", error="top-level JSON must be an object")

    try:
        solution = Solution.model_validate(data)
    except ValidationError as exc:
        return ParseResult(status="FAILURE", error=f"schema validation failed: {exc}")

    return ParseResult(status="SUCCESS", solution=solution)
