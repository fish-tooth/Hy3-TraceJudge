"""Tests for deterministic request cache and resume (P0-T05)."""
from __future__ import annotations

from src.cache import CacheRecord, JsonlCache, request_hash


def test_request_hash_deterministic_and_sensitive():
    msgs = [{"role": "user", "content": "hi"}]
    h1 = request_hash(model="m", messages=msgs, generation_config={"t": 0})
    h2 = request_hash(model="m", messages=msgs, generation_config={"t": 0})
    assert h1 == h2

    h3 = request_hash(model="m", messages=msgs, generation_config={"t": 1})
    assert h1 != h3

    h4 = request_hash(model="m2", messages=msgs, generation_config={"t": 0})
    assert h1 != h4

    h5 = request_hash(
        model="m", messages=[{"role": "user", "content": "bye"}], generation_config={"t": 0}
    )
    assert h1 != h5


def test_cache_second_hit_no_duplicate(tmp_path):
    cache = JsonlCache(tmp_path / "cache.jsonl")
    cache.put(CacheRecord(request_hash="k1", response="resp"))
    cache.put(CacheRecord(request_hash="k1", response="resp2"))
    assert len(cache) == 1
    assert cache.get("k1").response == "resp"


def test_cache_persists_and_reloads(tmp_path):
    p = tmp_path / "cache.jsonl"
    JsonlCache(p).put(CacheRecord(request_hash="k1", response="r"))
    cache2 = JsonlCache(p)
    assert "k1" in cache2
    assert cache2.get("k1").response == "r"


def test_cache_failure_record(tmp_path):
    p = tmp_path / "cache.jsonl"
    JsonlCache(p).put(CacheRecord(request_hash="k1", response=None, error="timeout"))
    rec = JsonlCache(p).get("k1")
    assert rec.error == "timeout"
    assert rec.response is None


def test_cache_skips_corrupt_lines(tmp_path):
    p = tmp_path / "cache.jsonl"
    p.write_text("not json\n", encoding="utf-8")
    cache = JsonlCache(p)
    assert len(cache) == 0
    cache.put(CacheRecord(request_hash="k1", response="r"))
    assert len(cache) == 1


def test_cache_metadata_preserved(tmp_path):
    p = tmp_path / "cache.jsonl"
    JsonlCache(p).put(
        CacheRecord(request_hash="k1", response="r", latency_ms=42.0, retry_count=2)
    )
    rec = JsonlCache(p).get("k1")
    assert rec.latency_ms == 42.0
    assert rec.retry_count == 2
