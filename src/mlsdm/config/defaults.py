"""Canonical defaults for cross-module configuration.

This module centralizes defaults that must remain consistent across runtime
configuration, API wiring, and documentation contracts.
"""

from __future__ import annotations

DEFAULT_CONFIG_PATH = "config/default_config.yaml"

RATE_LIMIT_REQUESTS_DEFAULT = 5
RATE_LIMIT_WINDOW_DEFAULT = 1
