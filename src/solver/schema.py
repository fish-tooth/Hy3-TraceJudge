"""Pydantic schemas for the structured, auditable math solver output (R4).

The solver must emit public, auditable steps (no hidden chain-of-thought), each
with a stable ``step_id``, a single main inference, and optional dependency hints.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class SolutionStep(BaseModel):
    """A single auditable inference step."""

    step_id: int = Field(..., ge=1, description="Stable 1-based step id.")
    statement: str = Field(..., min_length=1, description="Natural-language inference.")
    expression: str | None = Field(
        default=None, description="Optional math expression (LaTeX/plain)."
    )
    depends_on: list[int] = Field(
        default_factory=list, description="Ids of prerequisite steps."
    )

    @field_validator("depends_on")
    @classmethod
    def _no_self_dependency(cls, v: list[int], info: ValidationInfo) -> list[int]:
        step_id = info.data.get("step_id")
        if step_id is not None and step_id in v:
            raise ValueError("step cannot depend on itself")
        return v


class Solution(BaseModel):
    """A complete structured solution."""

    problem: str = Field(..., min_length=1)
    solution_steps: list[SolutionStep] = Field(..., min_length=1)
    final_answer: str = Field(..., min_length=1)

    @field_validator("solution_steps")
    @classmethod
    def _unique_step_ids(cls, v: list[SolutionStep]) -> list[SolutionStep]:
        ids = [s.step_id for s in v]
        if len(ids) != len(set(ids)):
            raise ValueError("step_id values must be unique")
        return v
