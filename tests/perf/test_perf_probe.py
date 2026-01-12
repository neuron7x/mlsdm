"""Lightweight perf probe to catch obvious regressions quickly."""

from __future__ import annotations

import os
import threading

import pytest
from fastapi.testclient import TestClient

from mlsdm.api.app import app
from mlsdm.config.perf_slo import DEFAULT_LATENCY_SLO
from tests.perf.utils import run_load_test

os.environ["DISABLE_RATE_LIMIT"] = "1"

_client_local = threading.local()


def _get_client() -> TestClient:
    client = getattr(_client_local, "client", None)
    if client is None:
        client = TestClient(app)
        _client_local.client = client
    return client


@pytest.mark.benchmark
class TestPerfProbe:
    """Fast perf probe for core endpoints."""

    def test_generate_perf_probe(self, deterministic_seed: int) -> None:
        """Ensure /generate stays within baseline latency in a tiny run."""

        def make_request() -> None:
            response = _get_client().post(
                "/generate",
                json={
                    "prompt": "Perf probe prompt",
                    "max_tokens": 32,
                    "moral_value": 0.6,
                },
            )
            assert response.status_code in (200, 201), f"Unexpected status: {response.status_code}"

        results = run_load_test(operation=make_request, n_requests=10, concurrency=2)

        assert results.p95_latency_ms < DEFAULT_LATENCY_SLO.api_p95_ms, (
            "Perf probe failed: P95 latency "
            f"{results.p95_latency_ms:.2f}ms exceeds SLO {DEFAULT_LATENCY_SLO.api_p95_ms}ms. "
            "Enable MLSDM_SLO_DEBUG=1 for per-request span timing."
        )

    def test_infer_perf_probe(self, deterministic_seed: int) -> None:
        """Ensure /infer stays within baseline latency in a tiny run."""

        def make_request() -> None:
            response = _get_client().post(
                "/infer",
                json={
                    "prompt": "Perf probe inference",
                    "max_tokens": 32,
                    "secure_mode": False,
                    "aphasia_mode": "off",
                    "rag_enabled": False,
                },
            )
            assert response.status_code in (200, 201), f"Unexpected status: {response.status_code}"

        results = run_load_test(operation=make_request, n_requests=10, concurrency=2)

        assert results.p95_latency_ms < DEFAULT_LATENCY_SLO.api_p95_ms, (
            "Perf probe failed: P95 latency "
            f"{results.p95_latency_ms:.2f}ms exceeds SLO {DEFAULT_LATENCY_SLO.api_p95_ms}ms. "
            "Enable MLSDM_SLO_DEBUG=1 for per-request span timing."
        )
