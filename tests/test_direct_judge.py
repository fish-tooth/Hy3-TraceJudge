"""Tests for B0 Direct Hy3 Judge (P1-T06)."""
from __future__ import annotations

from src.benchmark.processbench_adapter import CanonicalSample
from src.evaluator.direct_judge import (
    DirectJudge,
    build_judge_messages,
    parse_judge_raw,
)
from src.llm.mock_provider import MockProvider

PROMPT = "You are a judge."


def _sample(**kw) -> CanonicalSample:
    base = dict(
        sample_id="s1",
        problem="What is 1+1?",
        steps=["1+1=2", "so the answer is 2"],
        source="gsm8k",
        gold_process_correct=True,
        gold_first_error_step=None,
    )
    base.update(kw)
    return CanonicalSample(**base)


# --- parse_judge_raw ---------------------------------------------------------

def test_parse_correct_process():
    r = parse_judge_raw(
        '{"process_correct": true, "first_error_step": null, '
        '"error_type": null, "reason": "ok"}'
    )
    assert r.status == "SUCCESS"
    assert r.process_correct is True
    assert r.first_error_step is None
    assert r.error_type is None


def test_parse_error_process():
    r = parse_judge_raw(
        '{"process_correct": false, "first_error_step": 2, '
        '"error_type": "ARITHMETIC_ERROR", "reason": "wrong"}'
    )
    assert r.status == "SUCCESS"
    assert r.process_correct is False
    assert r.first_error_step == 2
    assert r.error_type == "ARITHMETIC_ERROR"


def test_parse_error_process_without_location():
    r = parse_judge_raw(
        '{"process_correct": false, "first_error_step": null, "reason": "somewhere"}'
    )
    assert r.status == "SUCCESS"
    assert r.process_correct is False
    assert r.first_error_step is None


def test_parse_strips_markdown_fence():
    raw = '```json\n{"process_correct": true, "first_error_step": null, "reason": "ok"}\n```'
    r = parse_judge_raw(raw)
    assert r.status == "SUCCESS"
    assert r.process_correct is True


def test_parse_extracts_json_from_prose():
    raw = 'Here is the answer: {"process_correct": false, "first_error_step": 1}'
    r = parse_judge_raw(raw)
    assert r.status == "SUCCESS"
    assert r.first_error_step == 1


def test_parse_rejects_non_json():
    r = parse_judge_raw("not json at all")
    assert r.status == "FAILURE"


def test_parse_rejects_missing_process_correct():
    r = parse_judge_raw('{"first_error_step": 1}')
    assert r.status == "FAILURE"


def test_parse_rejects_non_bool_process_correct():
    r = parse_judge_raw('{"process_correct": "yes", "first_error_step": null}')
    assert r.status == "FAILURE"


def test_parse_rejects_bool_first_error_step():
    r = parse_judge_raw('{"process_correct": false, "first_error_step": true}')
    assert r.status == "FAILURE"


def test_parse_rejects_non_positive_first_error_step():
    r = parse_judge_raw('{"process_correct": false, "first_error_step": 0}')
    assert r.status == "FAILURE"


def test_parse_rejects_inconsistent_correct_with_step():
    r = parse_judge_raw('{"process_correct": true, "first_error_step": 3}')
    assert r.status == "FAILURE"


# --- build_judge_messages ----------------------------------------------------

def test_build_messages_numbers_steps_from_one():
    s = _sample(steps=["alpha", "beta", "gamma"])
    msgs = build_judge_messages(s, PROMPT)
    assert msgs[0] == {"role": "system", "content": PROMPT}
    assert "Step 1: alpha" in msgs[1]["content"]
    assert "Step 2: beta" in msgs[1]["content"]
    assert "Step 3: gamma" in msgs[1]["content"]
    assert s.problem in msgs[1]["content"]


# --- DirectJudge end-to-end --------------------------------------------------

def test_judge_returns_prediction():
    raw = (
        '{"process_correct": false, "first_error_step": 1, '
        '"error_type": "LOGIC_GAP", "reason": "gap"}'
    )
    judge = DirectJudge(MockProvider([raw]), PROMPT, model="mock")
    pred = judge.judge(_sample())
    assert pred.sample_id == "s1"
    assert pred.process_correct is False
    assert pred.first_error_step == 1
    assert pred.error_type == "LOGIC_GAP"
    assert pred.parse_status == "SUCCESS"


def test_judge_parse_failure_recorded():
    judge = DirectJudge(MockProvider(["garbage"]), PROMPT, model="mock")
    pred = judge.judge(_sample())
    assert pred.parse_status == "FAILURE"
    assert pred.parse_error is not None
    assert pred.process_correct is None


def test_judge_api_failure_recorded():
    from src.llm.base import ProviderResult

    class _Failing(MockProvider):
        def complete(self, messages, **gen_cfg):
            self._call_count += 1
            return ProviderResult(raw=None, error="timeout", model="mock")

    judge = DirectJudge(_Failing(), PROMPT, model="mock")
    pred = judge.judge(_sample())
    assert pred.parse_status == "FAILURE"
    assert pred.error == "timeout"


def test_judge_preserves_reasoning():
    raw = (
        '{"process_correct": true, "first_error_step": null, '
        '"error_type": null, "reason": "ok"}'
    )
    judge = DirectJudge(
        MockProvider([raw], reasoning="hidden chain-of-thought"), PROMPT, model="mock"
    )
    pred = judge.judge(_sample())
    assert pred.parse_status == "SUCCESS"
    assert pred.reasoning == "hidden chain-of-thought"
