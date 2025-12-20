"""Deprecated service shim that delegates to the canonical MLSDM API app."""

from __future__ import annotations

import os

from fastapi import FastAPI

from mlsdm.api.app import app as _canonical_app
from mlsdm.api.app import create_app as _create_canonical_app
from mlsdm.entrypoints.serve import serve as _serve


def create_app() -> FastAPI:
    """Return the canonical FastAPI application."""
    return _create_canonical_app()


def main() -> None:
    """Start the canonical HTTP API server (legacy shim)."""
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    _serve(host=host, port=port)


__all__ = ["create_app", "main", "_canonical_app"]

