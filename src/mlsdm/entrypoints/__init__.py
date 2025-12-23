"""
MLSDM Runtime Entrypoints.

Provides a single canonical runtime entrypoint:
- mlsdm.entrypoints.serve:serve (invoked via `mlsdm serve`)

Mode wrappers delegate to `serve` with profile hints.
"""

from mlsdm.entrypoints.health import get_health_status, health_check, is_healthy

__all__ = [
    "health_check",
    "is_healthy",
    "get_health_status",
]
