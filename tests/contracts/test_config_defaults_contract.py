from __future__ import annotations

from mlsdm.config.calibration import RATE_LIMIT_DEFAULTS
from mlsdm.config.defaults import DEFAULT_CONFIG_PATH
from mlsdm.config.runtime import RuntimeMode, get_runtime_config


def test_runtime_defaults_use_canonical_constants(monkeypatch) -> None:
    monkeypatch.delenv("CONFIG_PATH", raising=False)
    monkeypatch.delenv("RATE_LIMIT_REQUESTS", raising=False)
    monkeypatch.delenv("RATE_LIMIT_WINDOW", raising=False)

    config = get_runtime_config(RuntimeMode.DEV)

    assert config.engine.config_path == DEFAULT_CONFIG_PATH
    assert config.security.rate_limit_requests == RATE_LIMIT_DEFAULTS.requests_per_window
    assert config.security.rate_limit_window == RATE_LIMIT_DEFAULTS.window_seconds
