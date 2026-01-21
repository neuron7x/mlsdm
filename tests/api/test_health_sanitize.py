"""Tests for health check sanitization in test/CI environments."""

from __future__ import annotations

import asyncio

from fastapi import Response


def test_readiness_sanitized_skips_psutil(monkeypatch) -> None:
    """Readiness should return 200 and avoid psutil when sanitization is enabled."""
    monkeypatch.setenv("MLSDM_CI_HEALTH_SANITIZE", "1")
    monkeypatch.setenv("MLSDM_ENV", "test")

    from mlsdm.api import health

    def _raise_psutil_call(*_args, **_kwargs) -> None:
        raise AssertionError("psutil should not be called when sanitization is enabled")

    monkeypatch.setattr(health.psutil, "virtual_memory", _raise_psutil_call)
    monkeypatch.setattr(health.psutil, "cpu_percent", _raise_psutil_call)

    response = Response()
    readiness = asyncio.run(health._compute_readiness(response))

    assert response.status_code == 200
    assert readiness.ready is True
    assert readiness.components["system_memory"].healthy is True
    assert readiness.components["system_cpu"].healthy is True
