"""Failure-mode tests for rate limit configuration."""

from __future__ import annotations

import importlib
import os
import sys

from mlsdm.config.defaults import RATE_LIMIT_REQUESTS_DEFAULT, RATE_LIMIT_WINDOW_DEFAULT


def test_invalid_rate_limit_env_falls_back_to_defaults() -> None:
    keys = ["RATE_LIMIT_REQUESTS", "RATE_LIMIT_WINDOW"]
    original = {key: os.environ.get(key) for key in keys}

    try:
        os.environ["RATE_LIMIT_REQUESTS"] = "0"
        os.environ["RATE_LIMIT_WINDOW"] = "0"

        sys.modules.pop("mlsdm.api.app", None)
        app_module = importlib.import_module("mlsdm.api.app")

        assert app_module._rate_limit_requests == RATE_LIMIT_REQUESTS_DEFAULT
        assert app_module._rate_limit_window == RATE_LIMIT_WINDOW_DEFAULT
    finally:
        for key, value in original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        sys.modules.pop("mlsdm.api.app", None)
        importlib.import_module("mlsdm.api.app")
