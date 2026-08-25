"""Math solver that produces structured, auditable solution steps via Hy3 (R1/R4)."""
from __future__ import annotations

from dataclasses import dataclass

from src.llm.base import BaseLLMProvider
from src.solver.parser import parse_solution
from src.solver.schema import Solution


@dataclass
class SolverResult:
    problem: str
    raw: str | None = None
    solution: Solution | None = None
    parse_status: str = "FAILURE"
    parse_error: str | None = None
    error: str | None = None
    latency_ms: float | None = None
    retry_count: int = 0

    @property
    def ok(self) -> bool:
        return self.solution is not None and self.error is None

    def to_dict(self) -> dict:
        return {
            "problem": self.problem,
            "raw": self.raw,
            "solution": self.solution.model_dump() if self.solution else None,
            "parse_status": self.parse_status,
            "parse_error": self.parse_error,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "retry_count": self.retry_count,
        }


class MathSolver:
    """Wrap a provider + parser to solve a problem into structured steps."""

    def __init__(self, provider: BaseLLMProvider, system_prompt: str) -> None:
        self._provider = provider
        self._system_prompt = system_prompt

    def solve(self, problem: str, **gen_cfg) -> SolverResult:
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": problem},
        ]
        result = self._provider.complete(messages, **gen_cfg)

        if not result.ok:
            return SolverResult(
                problem=problem,
                raw=result.raw,
                parse_status="FAILURE",
                parse_error=result.error,
                error=result.error,
                latency_ms=result.latency_ms,
                retry_count=result.retry_count,
            )

        parsed = parse_solution(result.raw or "")
        return SolverResult(
            problem=problem,
            raw=result.raw,
            solution=parsed.solution,
            parse_status=parsed.status,
            parse_error=parsed.error,
            error=result.error,
            latency_ms=result.latency_ms,
            retry_count=result.retry_count,
        )
