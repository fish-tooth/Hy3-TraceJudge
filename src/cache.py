"""Deterministic request cache (append-only JSONL) with resume support.

Cache key MUST include model + prompt/messages + relevant generation config so
that changing any of these invalidates the cached entry (EXT-08 / eval protocol 14.1).
"""
from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.run_metadata import stable_hash


def request_hash(*, model: str, messages: Any, generation_config: dict[str, Any]) -> str:
    """Deterministic hash of model + messages + generation config."""
    payload = {
        "model": model,
        "messages": messages,
        "generation_config": generation_config,
    }
    return stable_hash(payload)


@dataclass
class CacheRecord:
    request_hash: str
    response: Any
    latency_ms: float | None = None
    retry_count: int = 0
    error: str | None = None
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheRecord:
        return cls(**data)


class JsonlCache:
    """Append-only JSONL cache keyed by deterministic request hash.

    Thread-safe for append; idempotent writes (same hash is not duplicated).
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._lock = threading.Lock()
        self._index: dict[str, CacheRecord] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = CacheRecord.from_dict(json.loads(line))
                    self._index[rec.request_hash] = rec
                except (json.JSONDecodeError, TypeError):
                    # Skip corrupt lines rather than crashing the whole cache load.
                    continue

    def get(self, key: str) -> CacheRecord | None:
        return self._index.get(key)

    def put(self, record: CacheRecord) -> None:
        with self._lock:
            if record.request_hash in self._index:
                return  # idempotent: never duplicate the same request
            self._index[record.request_hash] = record
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def __contains__(self, key: str) -> bool:
        return key in self._index

    def __len__(self) -> int:
        return len(self._index)
