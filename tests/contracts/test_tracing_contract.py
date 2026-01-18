from __future__ import annotations

import logging

from mlsdm.observability import tracing
from mlsdm.observability.tracing import TracingConfig, initialize_tracing, shutdown_tracing


def test_tracing_initialization_does_not_crash(caplog) -> None:
    shutdown_tracing()

    caplog.set_level(logging.INFO)
    config = TracingConfig(enabled=True, exporter_type="otlp")
    initialize_tracing(config)

    if not tracing.OTEL_AVAILABLE:
        assert "OpenTelemetry is not installed" in caplog.text
