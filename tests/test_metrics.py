"""Tests for M1-M5 evaluator metrics (P1-T07)."""
from __future__ import annotations

from src.analysis.metrics import compute_metrics, group_by_source
from src.benchmark.processbench_adapter import CanonicalSample
from src.evaluator.direct_judge import JudgePrediction


def _gold(sid, *, correct: bool, first_error: int | None = None, source="gsm8k"):
    return CanonicalSample(
        sample_id=sid,
        problem=f"p{sid}",
        steps=["s1", "s2", "s3"],
        source=source,
        gold_process_correct=correct,
        gold_first_error_step=first_error,
    )


def _pred(sid, *, correct: bool | None, first_error: int | None = None,
          parse_status="SUCCESS", error=None):
    return JudgePrediction(
        sample_id=sid,
        process_correct=correct,
        first_error_step=first_error,
        parse_status=parse_status,
        error=error,
    )


def _scenario():
    golds = [
        _gold("g1", correct=False, first_error=2),
        _gold("g2", correct=False, first_error=1),
        _gold("g3", correct=False, first_error=3),
        _gold("g4", correct=True),
        _gold("g5", correct=True),
    ]
    preds = [
        _pred("g1", correct=False, first_error=2),  # exact hit
        _pred("g2", correct=False, first_error=2),  # detect but wrong step (dist 1)
        _pred("g3", correct=True, first_error=None),  # missed error
        _pred("g4", correct=True, first_error=None),  # correct accept
        _pred("g5", correct=False, first_error=5),  # false positive on correct
    ]
    return golds, preds


def test_m1_error_detection_recall():
    golds, preds = _scenario()
    m = compute_metrics(preds, golds)
    assert m.n_gold_error == 3
    assert m.error_detection_recall == 2 / 3


def test_m2_first_error_exact():
    golds, preds = _scenario()
    m = compute_metrics(preds, golds)
    assert m.first_error_exact == 1 / 3


def test_m3_correct_process_accuracy():
    golds, preds = _scenario()
    m = compute_metrics(preds, golds)
    assert m.n_gold_correct == 2
    assert m.correct_process_accuracy == 1 / 2


def test_m4_process_status_accuracy():
    golds, preds = _scenario()
    m = compute_metrics(preds, golds)
    assert m.process_status_accuracy == 3 / 5


def test_m5_official_composite():
    golds, preds = _scenario()
    m = compute_metrics(preds, golds)
    assert m.official_composite == 2 / 5


def test_plus_minus_one():
    golds, preds = _scenario()
    m = compute_metrics(preds, golds)
    assert m.plus_minus_one == 2 / 3


def test_mean_abs_step_distance_excludes_missed():
    golds, preds = _scenario()
    m = compute_metrics(preds, golds)
    assert m.mean_abs_step_distance == 0.5
    assert m.n_missed_localization == 1


def test_empty_inputs_yield_none_rates():
    m = compute_metrics([], [])
    assert m.n_all == 0
    assert m.error_detection_recall is None
    assert m.first_error_exact is None
    assert m.correct_process_accuracy is None
    assert m.process_status_accuracy is None
    assert m.official_composite is None


def test_all_correct_denominator_zero_for_error_metrics():
    golds = [_gold("a", correct=True), _gold("b", correct=True)]
    preds = [_pred("a", correct=True), _pred("b", correct=True)]
    m = compute_metrics(preds, golds)
    assert m.n_gold_error == 0
    assert m.error_detection_recall is None
    assert m.first_error_exact is None
    assert m.correct_process_accuracy == 1.0


def test_pred_missing_counted():
    golds = [_gold("a", correct=False, first_error=1)]
    preds = [None]
    m = compute_metrics(preds, golds)
    assert m.n_pred_missing == 1
    # pred None contributes nothing to the numerator, but the gold error sample
    # still counts in the denominator -> 0/1 == 0.0
    assert m.error_detection_recall == 0.0


def test_parse_and_api_failure_counted():
    golds = [_gold("a", correct=False, first_error=1)]
    preds = [_pred("a", correct=None, parse_status="FAILURE", error="timeout")]
    m = compute_metrics(preds, golds)
    assert m.n_parse_failure == 1
    assert m.n_api_failure == 1


def test_group_by_source():
    golds = [
        _gold("a", correct=False, first_error=1, source="math"),
        _gold("b", correct=True, source="math"),
        _gold("c", correct=False, first_error=2, source="gsm8k"),
    ]
    preds = [
        _pred("a", correct=False, first_error=1),
        _pred("b", correct=True),
        _pred("c", correct=False, first_error=2),
    ]
    groups = group_by_source(preds, golds)
    assert set(groups) == {"math", "gsm8k"}
    assert groups["math"].n_all == 2
    assert groups["math"].first_error_exact == 1.0
    assert groups["gsm8k"].first_error_exact == 1.0


def test_length_mismatch_zip_truncates_but_n_all_correct():
    # zip truncates; n_all reflects the shorter side, which is the documented behavior.
    golds = [_gold("a", correct=True), _gold("b", correct=True)]
    preds = [_pred("a", correct=True)]
    m = compute_metrics(preds, golds)
    assert m.n_all == 1


def test_to_dict_serializable():
    m = compute_metrics([], [])
    d = m.to_dict()
    assert isinstance(d, dict)
    assert d["n_all"] == 0
