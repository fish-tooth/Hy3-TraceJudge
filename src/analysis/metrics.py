"""Evaluator metrics (M1-M5) per evaluation_protocol §4.2 (P1-T07).

All rates are ``None`` when the denominator is zero, so empty subgroups are
reported honestly instead of producing a fake 0.0 or division error.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass

from src.benchmark.processbench_adapter import CanonicalSample
from src.evaluator.direct_judge import JudgePrediction


@dataclass
class MetricsResult:
    n_all: int = 0
    n_gold_error: int = 0
    n_gold_correct: int = 0
    # M1-M5
    error_detection_recall: float | None = None
    first_error_exact: float | None = None
    correct_process_accuracy: float | None = None
    process_status_accuracy: float | None = None
    official_composite: float | None = None
    # auxiliary localization
    plus_minus_one: float | None = None
    mean_abs_step_distance: float | None = None
    n_missed_localization: int = 0
    # failure accounting
    n_parse_failure: int = 0
    n_api_failure: int = 0
    n_pred_missing: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


def _rate(num: int, den: int) -> float | None:
    return num / den if den else None


def compute_metrics(
    predictions: Iterable[JudgePrediction | None],
    golds: Iterable[CanonicalSample],
) -> MetricsResult:
    """Compute M1-M5 for aligned predictions and golds (same order)."""
    pairs = list(zip(predictions, golds, strict=False))
    r = MetricsResult()
    r.n_all = len(pairs)

    det_hits = 0  # M1: error sample detected as error
    exact_hits = 0  # M2: first error exact
    correct_hits = 0  # M3: correct sample accepted as correct
    status_hits = 0  # M4: process status matched
    composite_hits = 0  # M5: official composite
    pm1_hits = 0  # |pred-gold| <= 1 on error samples
    abs_dist_sum = 0
    abs_dist_n = 0

    for pred, gold in pairs:
        if gold is None:
            continue

        # Gold-based denominators are counted regardless of pred availability,
        # so a missing/failed prediction still lands in the correct denominator.
        if gold.gold_process_correct:
            r.n_gold_correct += 1
        else:
            r.n_gold_error += 1

        if pred is None:
            r.n_pred_missing += 1
            continue

        if pred.parse_status == "FAILURE":
            r.n_parse_failure += 1
        if pred.error is not None:
            r.n_api_failure += 1

        if gold.gold_process_correct:
            # M3 / M4 / M5 for correct-process samples
            if pred.process_correct is True:
                correct_hits += 1
                status_hits += 1
                composite_hits += 1
            continue

        # gold process-invalid
        if pred.process_correct is False:
            det_hits += 1  # M1

        if pred.first_error_step is None:
            r.n_missed_localization += 1
        else:
            gold_step = gold.gold_first_error_step
            if gold_step is not None and pred.first_error_step == gold_step:
                exact_hits += 1  # M2
                composite_hits += 1  # M5
            if gold_step is not None:
                dist = abs(pred.first_error_step - gold_step)
                abs_dist_sum += dist
                abs_dist_n += 1
                if dist <= 1:
                    pm1_hits += 1

        # M4: process status (binary error vs correct) matched
        if pred.process_correct is False:
            status_hits += 1

    r.error_detection_recall = _rate(det_hits, r.n_gold_error)
    r.first_error_exact = _rate(exact_hits, r.n_gold_error)
    r.correct_process_accuracy = _rate(correct_hits, r.n_gold_correct)
    r.process_status_accuracy = _rate(status_hits, r.n_all)
    r.official_composite = _rate(composite_hits, r.n_all)
    r.plus_minus_one = _rate(pm1_hits, r.n_gold_error)
    r.mean_abs_step_distance = _rate(abs_dist_sum, abs_dist_n)
    return r


def group_by_source(
    predictions: Iterable[JudgePrediction | None],
    golds: Iterable[CanonicalSample],
) -> dict[str, MetricsResult]:
    """Compute per-source metric bundles (for split-level reporting)."""
    grouped: dict[str, list[JudgePrediction | None]] = {}
    grouped_golds: dict[str, list[CanonicalSample]] = {}
    for pred, gold in zip(predictions, golds, strict=False):
        if gold is None:
            continue
        grouped.setdefault(gold.source, []).append(pred)
        grouped_golds.setdefault(gold.source, []).append(gold)
    return {
        source: compute_metrics(grouped[source], grouped_golds[source])
        for source in grouped
    }
