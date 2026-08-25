"""Run metadata and deterministic hashing for reproducibility (EXT-08)."""
from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def stable_hash(obj: Any) -> str:
    """Deterministic SHA256 over a canonical JSON serialization.

    ``sort_keys=True`` + ``default=str`` keeps the hash stable across dict
    ordering and across minor type differences.
    """
    canonical = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def git_commit(repo: str | Path = ".") -> str:
    """Return the current git commit hash, or ``"unknown"`` if not available."""
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except Exception:
        pass
    return "unknown"


def new_run_id(prefix: str = "run") -> str:
    """Generate a unique, time-sortable run id."""
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    short = uuid.uuid4().hex[:8]
    return f"{prefix}-{ts}-{short}"


@dataclass
class RunMetadata:
    """Provenance for a single evaluation run (EXT-08 / reproducibility protocol)."""

    run_id: str
    git_commit: str
    created_at: str
    provider: str = "hy3"
    model: str = ""
    temperature: float = 0.0
    reasoning_setting: str = ""
    prompt_versions: dict[str, str] = field(default_factory=dict)
    config_hash: str = ""
    dataset_name: str = ""
    dataset_manifest_hash: str = ""
    seed: int = 42
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def dump(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunMetadata:
        return cls(**data)


def make_metadata(
    *,
    run_id: str,
    model: str,
    provider: str = "hy3",
    temperature: float = 0.0,
    reasoning_setting: str = "",
    prompt_versions: dict[str, str] | None = None,
    config: Any = None,
    dataset_name: str = "",
    dataset_manifest: Any = None,
    seed: int = 42,
    repo: str | Path = ".",
) -> RunMetadata:
    """Build a RunMetadata with hashes computed from inputs."""
    return RunMetadata(
        run_id=run_id,
        git_commit=git_commit(repo),
        created_at=datetime.now(UTC).isoformat(),
        provider=provider,
        model=model,
        temperature=temperature,
        reasoning_setting=reasoning_setting,
        prompt_versions=prompt_versions or {},
        config_hash=stable_hash(config) if config is not None else "",
        dataset_name=dataset_name,
        dataset_manifest_hash=(
            stable_hash(dataset_manifest) if dataset_manifest is not None else ""
        ),
        seed=seed,
    )
