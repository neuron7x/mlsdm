"""Contract tests for canonical defaults and invariant alignment."""

from __future__ import annotations

from pathlib import Path

from mlsdm.config.defaults import (
    DEFAULT_CONFIG_PATH,
    RATE_LIMIT_REQUESTS_DEFAULT,
    RATE_LIMIT_WINDOW_DEFAULT,
)
from mlsdm.config.runtime import RuntimeMode, get_runtime_config
from mlsdm.security.rate_limit import RateLimiter


def test_default_config_path_is_canonicalized() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source_root = repo_root / "src"
    allowed = {
        Path("src/mlsdm/config/defaults.py"),
        Path("src/mlsdm/entrypoints/dev_entry.py"),
    }

    hits = []
    for path in source_root.rglob("*.py"):
        if DEFAULT_CONFIG_PATH in path.read_text(encoding="utf-8"):
            hits.append(path.relative_to(repo_root))

    assert set(hits) <= allowed, f"Unexpected default config path references: {hits}"


def test_runtime_defaults_match_canonical_rate_limits() -> None:
    config = get_runtime_config(mode=RuntimeMode.DEV)
    assert config.security.rate_limit_requests == RATE_LIMIT_REQUESTS_DEFAULT
    assert config.security.rate_limit_window == RATE_LIMIT_WINDOW_DEFAULT


def test_rate_limiter_defaults_match_canonical_values() -> None:
    limiter = RateLimiter()
    assert limiter._requests_per_window == RATE_LIMIT_REQUESTS_DEFAULT
    assert limiter._window_seconds == RATE_LIMIT_WINDOW_DEFAULT
