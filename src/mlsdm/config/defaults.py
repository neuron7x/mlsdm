"""Canonical defaults shared across runtime and integration boundaries.

These defaults are shared across modules to prevent drift between runtime
entrypoints, API startup, and configuration loaders.
"""

from __future__ import annotations

DEFAULT_CONFIG_PATH = "config/default_config.yaml"
PRODUCTION_CONFIG_PATH = "config/production.yaml"

__all__ = [
    "DEFAULT_CONFIG_PATH",
    "PRODUCTION_CONFIG_PATH",
]
