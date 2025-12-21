"""Deprecated service shim that delegates to the canonical MLSDM API app."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from mlsdm.api.app import create_app as _create_canonical_app

if TYPE_CHECKING:
    from fastapi import FastAPI


def create_app() -> FastAPI:
    """Return the canonical FastAPI application."""
    return _create_canonical_app()


def main() -> None:
    """Start the canonical HTTP API server (legacy shim)."""
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    log_level = os.environ.get("LOG_LEVEL", "info")
    disable_rate_limit = os.environ.get("DISABLE_RATE_LIMIT") == "1"

    from mlsdm.serve import run_server

    run_server(
        mode="neuro",
        host=host,
        port=port,
        log_level=log_level,
        reload=False,
        config=None,
        backend=None,
        disable_rate_limit=disable_rate_limit,
    )


__all__ = ["create_app", "main"]
