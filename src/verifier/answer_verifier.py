"""Deterministic, non-LLM final-answer verification (R5.2 / R13).

Strategy chain (evaluation_protocol §5.1):
1. normalization
2. exact / canonical string
3. numeric equivalence
4. fraction / decimal / percentage
5. SymPy symbolic equivalence
6. unordered sets / roots
7. UNKNOWN

The verifier is precision-first: it returns ``UNKNOWN`` rather than guessing, and
``PARSE_ERROR`` for malformed/missing input. Neither is silently counted as wrong.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import sympy as sp
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)


class Verdict:
    EQUIVALENT = "EQUIVALENT"
    NOT_EQUIVALENT = "NOT_EQUIVALENT"
    UNKNOWN = "UNKNOWN"
    PARSE_ERROR = "PARSE_ERROR"


@dataclass
class VerdictResult:
    verdict: str
    strategy: str | None = None
    evidence: str = ""

    @property
    def is_equivalent(self) -> bool:
        return self.verdict == Verdict.EQUIVALENT


_NUM_TOLERANCE = 1e-9

_TRANSFORMATIONS = standard_transformations + (
    convert_xor,
    implicit_multiplication_application,
)


def normalize(text: str) -> str:
    """Lowercase, trim, unify unicode, and strip common wrappers."""
    s = text.strip().lower()
    # LaTeX math delimiters
    s = s.strip()
    if len(s) >= 2 and s[0] == "$" and s[-1] == "$":
        s = s[1:-1].strip()
    if s.startswith(r"\(") and s.endswith(r"\)"):
        s = s[2:-2].strip()
    # unify minus/dash characters
    s = s.replace("−", "-").replace("–", "-").replace("—", "-")
    s = s.replace("×", "*").replace("÷", "/").replace("−", "-")
    # remove thousands separators (commas between digits)
    s = re.sub(r"(?<=\d),(?=\d)", "", s)
    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    # strip a single trailing period (not part of a decimal)
    s = re.sub(r"(?<!\d)\.$", "", s)
    return s


def _strip_answer_prefix(s: str) -> str:
    """Remove common answer-introducing prefixes for a value-focused compare."""
    s = re.sub(r"^(?:the\s+)?(?:answer|result|solution|ans)\s*(?:is|:|=|->|=>)\s*", "", s)
    s = re.sub(r"^(?:final\s+answer|therefore|so|thus)\s*(?:is|:|=)?\s*", "", s)
    s = s.lstrip("=").strip()
    return s


def _try_float(s: str) -> float | None:
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _fraction_value(s: str) -> float | None:
    m = re.fullmatch(r"(-?\d+)\s*/\s*(-?\d+)", s)
    if m:
        den = int(m.group(2))
        if den == 0:
            return None
        return int(m.group(1)) / den
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)\s*%", s)
    if m:
        return float(m.group(1)) / 100.0
    return None


def _to_numeric(s: str) -> float | None:
    n = _try_float(s)
    if n is not None:
        return n
    return _fraction_value(s)


def _numbers_close(a: float, b: float) -> bool:
    if a == b:
        return True
    return abs(a - b) <= _NUM_TOLERANCE * max(1.0, abs(a), abs(b))


def _to_sympy(s: str) -> sp.Expr | None:
    try:
        return parse_expr(s, transformations=_TRANSFORMATIONS, evaluate=True)
    except Exception:
        return None


def _to_item_set(s: str) -> set[str] | None:
    t = s.strip()
    t = re.sub(r"^(?:answer|ans|solution)\s*[:=]\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"^[a-zA-Z]\s*(?:=|:|∈|in|is)\s*", "", t)
    if len(t) >= 2 and t[0] in "{[(" and t[-1] in "}])":
        t = t[1:-1]
    if "±" in t or "∓" in t:
        base = t.replace("±", "").replace("∓", "").strip()
        if base:
            return {"-" + base, base}
        return None
    parts = [p.strip() for p in re.split(r",|\bor\b|;|&", t)]
    parts = [p for p in parts if p]
    if len(parts) <= 1:
        return None
    return {normalize(p) for p in parts}


def verify(predicted: str | None, gold: str | None) -> VerdictResult:
    """Determine whether ``predicted`` matches ``gold`` (precision-first)."""
    if predicted is None or gold is None:
        return VerdictResult(Verdict.PARSE_ERROR, evidence="missing predicted or gold value")

    pred = normalize(str(predicted))
    gold = normalize(str(gold))

    if pred == "" or gold == "":
        return VerdictResult(Verdict.PARSE_ERROR, evidence="empty value after normalization")

    # 2. exact / canonical string
    if pred == gold:
        return VerdictResult(Verdict.EQUIVALENT, "exact")

    pred_val = _strip_answer_prefix(pred)
    gold_val = _strip_answer_prefix(gold)
    if pred_val == gold_val:
        return VerdictResult(Verdict.EQUIVALENT, "exact")

    # 3. numeric
    pred_num = _to_numeric(pred_val)
    gold_num = _to_numeric(gold_val)
    if pred_num is not None and gold_num is not None:
        if _numbers_close(pred_num, gold_num):
            return VerdictResult(Verdict.EQUIVALENT, "numeric")
        return VerdictResult(Verdict.NOT_EQUIVALENT, "numeric", f"{pred_num} != {gold_num}")

    # 5. SymPy symbolic equivalence
    pred_expr = _to_sympy(pred_val)
    gold_expr = _to_sympy(gold_val)
    if pred_expr is not None and gold_expr is not None:
        try:
            diff = sp.simplify(sp.expand(pred_expr - gold_expr))
        except Exception:
            diff = None
        if diff is not None and diff == 0:
            return VerdictResult(Verdict.EQUIVALENT, "sympy")
        if diff is not None and diff.is_Number:
            return VerdictResult(
                Verdict.NOT_EQUIVALENT, "sympy", f"symbolic difference = {diff}"
            )
        # non-constant symbolic difference: cannot be certain -> fall through

    # 6. unordered sets / roots
    pred_set = _to_item_set(pred_val)
    gold_set = _to_item_set(gold_val)
    if pred_set is not None and gold_set is not None:
        if pred_set == gold_set:
            return VerdictResult(Verdict.EQUIVALENT, "set")
        # numeric set comparison
        try:
            pred_nums = {_to_numeric(p) for p in pred_set}
            gold_nums = {_to_numeric(g) for g in gold_set}
            if (
                None not in pred_nums
                and None not in gold_nums
                and len(pred_nums) == len(pred_set)
                and len(gold_nums) == len(gold_set)
            ):
                if all(
                    any(_numbers_close(p, g) for g in gold_nums) for p in pred_nums
                ) and len(pred_nums) == len(gold_nums):
                    return VerdictResult(Verdict.EQUIVALENT, "set:numeric")
        except (TypeError, ValueError):
            pass
        return VerdictResult(Verdict.NOT_EQUIVALENT, "set", "sets differ")

    return VerdictResult(Verdict.UNKNOWN, evidence="no deterministic strategy decided")
