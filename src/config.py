"""Configuration loading with environment-variable overrides for secrets.

Security (EXT-12): the API key is read ONLY from the environment (or a local
``.env`` file that is git-ignored). A subset of values can be overridden by
environment variables so that no secret or endpoint-specific value is ever
hard-coded in the repository.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class ConfigError(RuntimeError):
    """Raised when configuration is missing, malformed, or incomplete."""


# Mapping of environment variable name -> dotted path inside the config dict.
# These override values from the YAML file (highest precedence for secrets).
_ENV_OVERRIDES: dict[str, str] = {
    "HY3_API_KEY": "provider.api_key",
    "HY3_BASE_URL": "provider.base_url",
    "HY3_MODEL": "provider.model",
}


def _get_nested(data: dict[str, Any], dotted: str) -> Any:
    cur: Any = data
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _set_nested(data: dict[str, Any], dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur = data
    for part in parts[:-1]:
        cur = cur.setdefault(part, {})
    cur[parts[-1]] = value


@dataclass
class Config:
    """Loaded configuration exposing convenient accessors over the raw dict."""

    data: dict[str, Any]
    config_path: Path
    _env_applied: dict[str, str] = field(default_factory=dict)

    # -- provider ----------------------------------------------------------
    @property
    def provider(self) -> dict[str, Any]:
        return self.data.get("provider", {})

    @property
    def api_key(self) -> str:
        return str(self.provider.get("api_key") or "")

    @property
    def base_url(self) -> str | None:
        return self.provider.get("base_url")

    @property
    def model(self) -> str | None:
        return self.provider.get("model")

    # -- generation --------------------------------------------------------
    @property
    def generation(self) -> dict[str, Any]:
        return self.data.get("generation", {})

    # -- run / cache / paths ----------------------------------------------
    @property
    def seed(self) -> int:
        return int(self.data.get("run", {}).get("seed", 42))

    @property
    def cache(self) -> dict[str, Any]:
        return self.data.get("cache", {})

    @property
    def paths(self) -> dict[str, Any]:
        return self.data.get("paths", {})

    def require_api_key(self) -> str:
        """Return the API key or raise ConfigError if absent.

        Called at the boundary where a real Hy3 call is about to be made, so a
        missing key fails fast and loudly instead of silently.
        """
        key = self.api_key
        if not key:
            raise ConfigError(
                "Hy3 API key is missing. Set HY3_API_KEY in the environment "
                "(or in a local .env file) before running. See .env.example."
            )
        return key

    def to_dict(self) -> dict[str, Any]:
        return self.data


def load_config(path: str | Path | None = None) -> Config:
    """Load YAML config and apply environment-variable overrides.

    Precedence (highest wins): environment variables > YAML file > defaults.
    """
    load_dotenv()  # no-op if .env is absent

    config_path = Path(path) if path else Path("configs/default.yaml")
    config_path = config_path.resolve()

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ConfigError(f"Config file must contain a YAML mapping: {config_path}")

    env_applied: dict[str, str] = {}
    for env_var, dotted in _ENV_OVERRIDES.items():
        value = os.environ.get(env_var)
        if value is not None and value != "":
            _set_nested(data, dotted, value)
            env_applied[env_var] = dotted

    return Config(data=data, config_path=config_path, _env_applied=env_applied)
