"""Tests for run metadata and deterministic hashing (P0-T04)."""
from __future__ import annotations

import json

from src.run_metadata import RunMetadata, make_metadata, new_run_id, stable_hash


def test_stable_hash_deterministic():
    assert stable_hash({"b": 2, "a": 1}) == stable_hash({"a": 1, "b": 2})


def test_stable_hash_sensitive_to_change():
    assert stable_hash({"x": 1}) != stable_hash({"x": 2})


def test_new_run_id_unique():
    ids = {new_run_id() for _ in range(200)}
    assert len(ids) == 200
    assert all(i.startswith("run-") for i in ids)


def test_config_hash_stable_for_same_config():
    m1 = make_metadata(run_id="r1", model="m", config={"a": 1, "b": [1, 2]})
    m2 = make_metadata(run_id="r2", model="m", config={"b": [1, 2], "a": 1})
    assert m1.config_hash == m2.config_hash


def test_config_hash_differs_on_change():
    m1 = make_metadata(run_id="r1", model="m", config={"a": 1})
    m2 = make_metadata(run_id="r2", model="m", config={"a": 2})
    assert m1.config_hash != m2.config_hash


def test_prompt_versions_preserved():
    m = make_metadata(run_id="r", model="m", prompt_versions={"solver": "abc123"})
    assert m.prompt_versions == {"solver": "abc123"}


def test_metadata_roundtrip(tmp_path):
    m = make_metadata(
        run_id="r1",
        model="m",
        prompt_versions={"solver": "abc"},
        dataset_manifest=["s1", "s2"],
        seed=7,
    )
    p = m.dump(tmp_path / "meta.json")
    loaded = RunMetadata.from_dict(json.loads(p.read_text(encoding="utf-8")))
    assert loaded.run_id == m.run_id
    assert loaded.model == m.model
    assert loaded.prompt_versions == m.prompt_versions
    assert loaded.dataset_manifest_hash == m.dataset_manifest_hash
    assert loaded.seed == 7
