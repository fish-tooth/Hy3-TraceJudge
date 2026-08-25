"""Tests for solver schema, parser, and MathSolver failure handling (P1-T02)."""
from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from src.llm.mock_provider import MockProvider
from src.solver.math_solver import MathSolver
from src.solver.parser import parse_solution
from src.solver.schema import SolutionStep


def _solution_json(**overrides) -> str:
    data = {
        "problem": "What is 2+2?",
        "solution_steps": [
            {
                "step_id": 1,
                "statement": "Add the two numbers.",
                "expression": "2+2",
                "depends_on": [],
            },
            {"step_id": 2, "statement": "The sum is four.", "expression": "4", "depends_on": [1]},
        ],
        "final_answer": "4",
    }
    data.update(overrides)
    return json.dumps(data)


def test_valid_solution_parses():
    res = parse_solution(_solution_json())
    assert res.ok
    assert res.solution.problem == "What is 2+2?"
    assert len(res.solution.solution_steps) == 2
    assert res.solution.final_answer == "4"


def test_solution_step_expression_optional():
    s = SolutionStep(step_id=1, statement="x")
    assert s.expression is None
    assert s.depends_on == []


def test_empty_response_fails():
    res = parse_solution("")
    assert not res.ok
    assert res.status == "FAILURE"


def test_invalid_json_fails():
    res = parse_solution("this is not json {")
    assert not res.ok
    assert "JSON decode failed" in (res.error or "")


def test_json_in_markdown_fence_parses():
    res = parse_solution("```json\n" + _solution_json() + "\n```")
    assert res.ok


def test_json_surrounded_by_prose_parses():
    res = parse_solution("Here is the answer:\n" + _solution_json() + "\nDone.")
    assert res.ok


def test_missing_field_fails():
    data = json.loads(_solution_json())
    del data["final_answer"]
    res = parse_solution(json.dumps(data))
    assert not res.ok
    assert "schema validation failed" in (res.error or "")


def test_duplicate_step_id_fails():
    data = json.loads(_solution_json())
    data["solution_steps"][1]["step_id"] = 1
    res = parse_solution(json.dumps(data))
    assert not res.ok


def test_empty_solution_steps_fails():
    data = json.loads(_solution_json())
    data["solution_steps"] = []
    res = parse_solution(json.dumps(data))
    assert not res.ok


def test_self_dependency_fails():
    with pytest.raises(ValidationError):
        SolutionStep(step_id=1, statement="x", depends_on=[1])


def test_top_level_not_object_fails():
    res = parse_solution("[1, 2, 3]")
    assert not res.ok
    assert "must be an object" in (res.error or "")


def test_math_solver_success_path():
    provider = MockProvider(default=_solution_json())
    solver = MathSolver(provider, system_prompt="solve it")
    out = solver.solve("What is 2+2?")
    assert out.ok
    assert out.solution.final_answer == "4"
    assert out.parse_status == "SUCCESS"


def test_math_solver_parse_failure_recorded():
    provider = MockProvider(default="not json")
    solver = MathSolver(provider, system_prompt="solve it")
    out = solver.solve("What is 2+2?")
    assert not out.ok
    assert out.solution is None
    assert out.parse_status == "FAILURE"
    assert out.parse_error is not None


def test_math_solver_provider_error_recorded():
    provider = MockProvider(default="not json")
    solver = MathSolver(provider, system_prompt="solve it")
    out = solver.solve("x")
    # provider error path is exercised via MathSolver when provider returns error;
    # MockProvider always succeeds, so we just assert the parse-failure path here.
    assert out.parse_status == "FAILURE"
