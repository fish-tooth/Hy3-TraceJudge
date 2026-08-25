"""ProcessBench -> canonical sample adapter (P1-T05 / EXT-02).

Preflight-confirmed schema (``Qwen/ProcessBench``, config ``default``):

    columns: ['id', 'generator', 'problem', 'steps', 'final_answer_correct', 'label']
    splits:  gsm8k (400), math (1000), olympiadbench (1000), omnimath (1000)

Label semantics (0-indexed, confirmed by preflight on 2026-08-24):

    label == -1   -> process fully correct  -> gold_first_error_step = None
    label == k>=0 -> first error at 0-based step k -> canonical 1-based step k + 1

This module is the ONLY place external ``-1`` / ``0-based`` encodings are
translated into the internal canonical ``first_error_step: int(1-based) | None``.
The core evaluator must never see raw 0-based or -1 labels.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CanonicalSample:
    """Unified internal representation of a ProcessBench sample."""

    sample_id: str
    problem: str
    steps: list[str]
    source: str
    generator: str = ""
    gold_process_correct: bool = False
    gold_first_error_step: int | None = None  # 1-based; None means fully correct
    gold_final_answer_correct: bool | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def gold_has_error(self) -> bool:
        return not self.gold_process_correct


def to_canonical(row: dict[str, Any], *, source: str) -> CanonicalSample:
    """Convert a raw ProcessBench row into a :class:`CanonicalSample`.

    ``source`` is the dataset split name (gsm8k / math / olympiadbench / omnimath)
    because the raw row has no explicit ``source`` column.
    """
    sample_id = str(row["id"])
    problem = str(row["problem"])
    steps = [str(s) for s in row["steps"]]
    label = int(row["label"])
    final_answer_correct = row.get("final_answer_correct")
    generator = str(row.get("generator") or "")

    if label == -1:
        gold_process_correct = True
        gold_first_error_step: int | None = None
    elif label >= 0:
        gold_process_correct = False
        gold_first_error_step = label + 1  # 0-based -> 1-based
    else:
        raise ValueError(
            f"Unexpected ProcessBench label {label!r} for sample {sample_id!r}; "
            "expected -1 (correct) or a 0-based step index."
        )

    return CanonicalSample(
        sample_id=sample_id,
        problem=problem,
        steps=steps,
        source=source,
        generator=generator,
        gold_process_correct=gold_process_correct,
        gold_first_error_step=gold_first_error_step,
        gold_final_answer_correct=(
            bool(final_answer_correct) if final_answer_correct is not None else None
        ),
        metadata={"label": label},
    )
