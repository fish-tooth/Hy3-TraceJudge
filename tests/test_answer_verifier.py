"""Tests for the deterministic Answer Verifier (P1-T03, tests-first >=50 cases)."""
from __future__ import annotations

import pytest

from src.verifier.answer_verifier import Verdict, normalize, verify

# --- normalization ----------------------------------------------------------

def test_normalize_lowercases_and_trims():
    assert normalize("  ABC  ") == "abc"


def test_normalize_unicode_minus():
    assert normalize("−3") == "-3"


def test_normalize_removes_thousands_comma():
    assert normalize("1,000") == "1000"


def test_normalize_strips_latex_dollars():
    assert normalize("$x$") == "x"


# --- exact ---------------------------------------------------------------

def test_exact_same():
    assert verify("4", "4").verdict == Verdict.EQUIVALENT


def test_exact_case_insensitive():
    assert verify("TRUE", "true").verdict == Verdict.EQUIVALENT


def test_exact_answer_prefix():
    assert verify("the answer is 4", "4").verdict == Verdict.EQUIVALENT


def test_exact_answer_colon():
    assert verify("Answer: 42", "42").verdict == Verdict.EQUIVALENT


# --- numeric -------------------------------------------------------------

@pytest.mark.parametrize(
    "pred,gold",
    [
        ("4", "4.0"),
        ("4.0", "4"),
        ("-3", "-3.0"),
        ("0", "0.0"),
        ("4.", "4"),
        ("3.140", "3.14"),
        ("1e3", "1000"),
        ("0.333333333", "1/3"),
        ("-0.5", "-1/2"),
    ],
)
def test_numeric_equivalent(pred, gold):
    assert verify(pred, gold).verdict == Verdict.EQUIVALENT


@pytest.mark.parametrize(
    "pred,gold",
    [
        ("4", "5"),
        ("4", "4.1"),
        ("0.5", "0.6"),
        ("2", "3"),
        ("-3", "3"),
        ("7", "8"),
        ("1e3", "1001"),
    ],
)
def test_numeric_not_equivalent(pred, gold):
    assert verify(pred, gold).verdict == Verdict.NOT_EQUIVALENT


# --- fraction / decimal / percentage -------------------------------------

@pytest.mark.parametrize(
    "pred,gold",
    [
        ("1/2", "0.5"),
        ("0.5", "50%"),
        ("50%", "1/2"),
        ("1/3", "2/6"),
        ("3/4", "75%"),
        ("1/2", "2/4"),
        ("25%", "0.25"),
    ],
)
def test_fraction_percentage_equivalent(pred, gold):
    assert verify(pred, gold).verdict == Verdict.EQUIVALENT


@pytest.mark.parametrize(
    "pred,gold",
    [
        ("1/2", "1/3"),
        ("1/2", "2"),
        ("100%", "0.5"),
        ("1/3", "1/4"),
        ("50%", "0.6"),
    ],
)
def test_fraction_percentage_not_equivalent(pred, gold):
    assert verify(pred, gold).verdict == Verdict.NOT_EQUIVALENT


# --- SymPy symbolic -------------------------------------------------------

@pytest.mark.parametrize(
    "pred,gold",
    [
        ("x^2 - 1", "(x-1)(x+1)"),
        ("2x", "2*x"),
        ("x+1", "1+x"),
        ("sqrt(4)", "2"),
        ("(x+1)^2", "x^2 + 2x + 1"),
        ("x*(x+1)", "x^2 + x"),
    ],
)
def test_sympy_equivalent(pred, gold):
    assert verify(pred, gold).verdict == Verdict.EQUIVALENT


@pytest.mark.parametrize(
    "pred,gold",
    [
        ("x+1", "x+2"),
        ("x^2", "x^2 + 1"),
        ("sqrt(4)", "3"),
        ("x-1", "x+1"),
    ],
)
def test_sympy_not_equivalent(pred, gold):
    assert verify(pred, gold).verdict == Verdict.NOT_EQUIVALENT


# --- unordered sets / roots ------------------------------------------------

@pytest.mark.parametrize(
    "pred,gold",
    [
        ("1, 2", "2, 1"),
        ("x = 1, 2", "2, 1"),
        ("±1", "-1, 1"),
        ("{1, 2}", "2, 1"),
        ("1 or 2", "2 or 1"),
        ("-1, 1", "1, -1"),
    ],
)
def test_set_equivalent(pred, gold):
    assert verify(pred, gold).verdict == Verdict.EQUIVALENT


@pytest.mark.parametrize(
    "pred,gold",
    [
        ("1, 2", "1, 3"),
        ("1, 2", "1, 2, 3"),
        ("±1", "±2"),
        ("-1, 1", "0, 1"),
    ],
)
def test_set_not_equivalent(pred, gold):
    assert verify(pred, gold).verdict == Verdict.NOT_EQUIVALENT


# --- UNKNOWN ---------------------------------------------------------------

@pytest.mark.parametrize(
    "pred,gold",
    [
        ("blue", "red"),
        ("x", "y"),
        ("the car", "the cat"),
        ("sin(x)", "cos(x)"),
        ("a", "b"),
        ("cat", "dog"),
    ],
)
def test_unknown(pred, gold):
    assert verify(pred, gold).verdict == Verdict.UNKNOWN


# --- PARSE_ERROR ------------------------------------------------------------

@pytest.mark.parametrize(
    "pred,gold",
    [
        (None, "4"),
        ("4", None),
        (None, None),
        ("", "4"),
        ("4", ""),
        ("   ", "4"),
    ],
)
def test_parse_error(pred, gold):
    assert verify(pred, gold).verdict == Verdict.PARSE_ERROR


# --- distinct classes are distinguishable -----------------------------------

def test_unknown_distinct_from_parse_error():
    assert Verdict.UNKNOWN != Verdict.PARSE_ERROR


def test_result_is_equivalent_property():
    assert verify("4", "4").is_equivalent is True
    assert verify("4", "5").is_equivalent is False
