"""Tests for the ProcessBench -> canonical adapter (P1-T05, off-by-one critical)."""
from __future__ import annotations

import pytest

from src.benchmark.processbench_adapter import to_canonical


def _row(**overrides):
    base = {
        "id": "gsm8k-0",
        "generator": "generator-model",
        "problem": "What is 1+1?",
        "steps": ["step A", "step B", "step C"],
        "final_answer_correct": False,
        "label": 1,
    }
    base.update(overrides)
    return base


# --- no-error (label == -1) -> null -----------------------------------------

def test_label_minus_one_maps_to_correct_and_null():
    s = to_canonical(_row(label=-1, final_answer_correct=True), source="gsm8k")
    assert s.gold_process_correct is True
    assert s.gold_has_error is False
    assert s.gold_first_error_step is None


# --- 0-based -> 1-based (the critical off-by-one) ----------------------------

def test_label_zero_maps_to_first_step():
    s = to_canonical(_row(label=0), source="gsm8k")
    assert s.gold_process_correct is False
    assert s.gold_first_error_step == 1


def test_label_one_maps_to_second_step():
    s = to_canonical(_row(label=1), source="gsm8k")
    assert s.gold_process_correct is False
    assert s.gold_first_error_step == 2


def test_label_three_maps_to_fourth_step():
    s = to_canonical(_row(label=3), source="math")
    assert s.gold_first_error_step == 4


def test_label_seven_maps_to_eighth_step():
    s = to_canonical(_row(label=7), source="olympiadbench")
    assert s.gold_first_error_step == 8


# --- field passthrough -------------------------------------------------------

def test_fields_are_preserved():
    s = to_canonical(
        _row(
            id="math-42",
            problem="Solve x+2=5",
            steps=["S1", "S2"],
            generator="gpt4o",
            final_answer_correct=False,
            label=0,
        ),
        source="math",
    )
    assert s.sample_id == "math-42"
    assert s.problem == "Solve x+2=5"
    assert s.steps == ["S1", "S2"]
    assert s.generator == "gpt4o"
    assert s.source == "math"
    assert s.gold_final_answer_correct is False
    assert s.metadata == {"label": 0}


def test_source_is_taken_from_argument_not_row():
    s = to_canonical(_row(label=-1), source="omnimath")
    assert s.source == "omnimath"


# --- invalid label -----------------------------------------------------------

def test_invalid_label_raises():
    with pytest.raises(ValueError):
        to_canonical(_row(label=-2), source="gsm8k")


# --- final_answer_correct coercion -------------------------------------------

def test_final_answer_correct_bool_coercion():
    s = to_canonical(_row(final_answer_correct=True, label=-1), source="gsm8k")
    assert s.gold_final_answer_correct is True


def test_final_answer_correct_none_when_missing():
    row = _row(label=-1)
    row.pop("final_answer_correct")
    s = to_canonical(row, source="gsm8k")
    assert s.gold_final_answer_correct is None
