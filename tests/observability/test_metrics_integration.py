"""
Integration tests for Prometheus metrics.

These tests verify that metrics are properly collected and exported
across the MLSDM pipeline without requiring external Prometheus server.

Coverage:
- Metrics registration (counters, gauges, histograms)
- Metric values after multiple operations
- Prometheus text format export
- MetricsRegistry for engine-level tracking
"""

import pytest
from prometheus_client import CollectorRegistry

from mlsdm.observability.metrics import (
    MetricsExporter,
    MetricsRegistry,
    get_metrics_exporter,
)


@pytest.fixture
def isolated_metrics():
    """Create isolated MetricsExporter with its own registry."""
    registry = CollectorRegistry()
    return MetricsExporter(registry=registry)


@pytest.fixture
def isolated_registry():
    """Create isolated MetricsRegistry for engine metrics."""
    return MetricsRegistry()


class TestMetricsIntegrationCounters:
    """Tests for counter metrics after operations."""

    def test_events_processed_increases_after_operations(self, isolated_metrics):
        """Test that events_processed counter increases correctly."""
        # Initial value should be 0
        initial = isolated_metrics.events_processed._value.get()
        assert initial == 0

        # Simulate processing events
        for _ in range(5):
            isolated_metrics.increment_events_processed()

        # Verify counter increased
        final = isolated_metrics.events_processed._value.get()
        assert final == 5

    def test_events_rejected_tracks_moral_rejections(self, isolated_metrics):
        """Test that events_rejected tracks moral filter rejections."""
        isolated_metrics.increment_events_rejected()
        isolated_metrics.increment_events_rejected()
        isolated_metrics.increment_events_rejected()

        assert isolated_metrics.events_rejected._value.get() == 3

    def test_moral_rejections_by_reason(self, isolated_metrics):
        """Test moral rejection counter with reason labels."""
        isolated_metrics.increment_moral_rejection("below_threshold", 5)
        isolated_metrics.increment_moral_rejection("sleep_phase", 2)
        isolated_metrics.increment_moral_rejection("below_threshold", 3)

        # Check values with labels
        below_threshold = isolated_metrics.moral_rejections.labels(
            reason="below_threshold"
        )._value.get()
        sleep_phase = isolated_metrics.moral_rejections.labels(
            reason="sleep_phase"
        )._value.get()

        assert below_threshold == 8
        assert sleep_phase == 2

    def test_aphasia_detection_by_severity(self, isolated_metrics):
        """Test aphasia detection counter by severity bucket."""
        # Simulate aphasia detections at various severities
        isolated_metrics.increment_aphasia_detected("low", 10)
        isolated_metrics.increment_aphasia_detected("medium", 5)
        isolated_metrics.increment_aphasia_detected("high", 2)
        isolated_metrics.increment_aphasia_detected("critical", 1)

        # Verify counts
        low = isolated_metrics.aphasia_detected_total.labels(
            severity_bucket="low"
        )._value.get()
        medium = isolated_metrics.aphasia_detected_total.labels(
            severity_bucket="medium"
        )._value.get()
        high = isolated_metrics.aphasia_detected_total.labels(
            severity_bucket="high"
        )._value.get()
        critical = isolated_metrics.aphasia_detected_total.labels(
            severity_bucket="critical"
        )._value.get()

        assert low == 10
        assert medium == 5
        assert high == 2
        assert critical == 1

    def test_requests_by_endpoint_and_status(self, isolated_metrics):
        """Test request counter with endpoint and status labels."""
        # Simulate requests
        isolated_metrics.increment_requests("/generate", "2xx", 100)
        isolated_metrics.increment_requests("/generate", "4xx", 5)
        isolated_metrics.increment_requests("/infer", "2xx", 50)
        isolated_metrics.increment_requests("/infer", "5xx", 2)

        # Verify
        gen_2xx = isolated_metrics.requests_total.labels(
            endpoint="/generate", status="2xx"
        )._value.get()
        gen_4xx = isolated_metrics.requests_total.labels(
            endpoint="/generate", status="4xx"
        )._value.get()
        infer_2xx = isolated_metrics.requests_total.labels(
            endpoint="/infer", status="2xx"
        )._value.get()

        assert gen_2xx == 100
        assert gen_4xx == 5
        assert infer_2xx == 50


class TestMetricsIntegrationGauges:
    """Tests for gauge metrics."""

    def test_phase_gauge_reflects_wake_sleep(self, isolated_metrics):
        """Test that phase gauge reflects wake/sleep transitions."""
        # Set to wake
        isolated_metrics.set_phase("wake")
        assert isolated_metrics.phase_gauge._value.get() == 1.0

        # Set to sleep
        isolated_metrics.set_phase("sleep")
        assert isolated_metrics.phase_gauge._value.get() == 0.0

        # Back to wake
        isolated_metrics.set_phase("wake")
        assert isolated_metrics.phase_gauge._value.get() == 1.0

    def test_moral_threshold_gauge(self, isolated_metrics):
        """Test moral threshold gauge updates."""
        isolated_metrics.set_moral_threshold(0.5)
        assert isolated_metrics.moral_threshold._value.get() == 0.5

        isolated_metrics.set_moral_threshold(0.75)
        assert isolated_metrics.moral_threshold._value.get() == 0.75

    def test_memory_usage_gauge(self, isolated_metrics):
        """Test memory usage gauge updates."""
        isolated_metrics.set_memory_usage(1024 * 1024 * 100)  # 100 MB
        assert isolated_metrics.current_memory_usage._value.get() == 1024 * 1024 * 100

    def test_emergency_shutdown_gauge(self, isolated_metrics):
        """Test emergency shutdown active gauge."""
        # Not in shutdown
        isolated_metrics.set_emergency_shutdown_active(False)
        assert isolated_metrics.emergency_shutdown_active._value.get() == 0.0

        # In shutdown
        isolated_metrics.set_emergency_shutdown_active(True)
        assert isolated_metrics.emergency_shutdown_active._value.get() == 1.0

    def test_stateless_mode_gauge(self, isolated_metrics):
        """Test stateless mode gauge."""
        isolated_metrics.set_stateless_mode(False)
        assert isolated_metrics.stateless_mode._value.get() == 0.0

        isolated_metrics.set_stateless_mode(True)
        assert isolated_metrics.stateless_mode._value.get() == 1.0


class TestMetricsIntegrationHistograms:
    """Tests for histogram metrics."""

    def test_generation_latency_histogram(self, isolated_metrics):
        """Test generation latency histogram observations."""
        latencies = [50, 100, 150, 200, 250]
        for lat in latencies:
            isolated_metrics.observe_generation_latency(float(lat))

        # Check histogram count
        metrics_text = isolated_metrics.get_metrics_text()
        assert "mlsdm_generation_latency_milliseconds_count 5" in metrics_text

    def test_request_latency_with_labels(self, isolated_metrics):
        """Test request latency histogram with endpoint and phase labels."""
        # Record latencies
        isolated_metrics.observe_request_latency_seconds(0.1, "/generate", "wake")
        isolated_metrics.observe_request_latency_seconds(0.2, "/generate", "wake")
        isolated_metrics.observe_request_latency_seconds(0.5, "/infer", "sleep")

        metrics_text = isolated_metrics.get_metrics_text()

        # Verify histogram has data
        assert "mlsdm_request_latency_seconds" in metrics_text
        assert 'endpoint="/generate"' in metrics_text
        assert 'phase="wake"' in metrics_text

    def test_processing_latency_timer(self, isolated_metrics):
        """Test processing latency timer API."""
        import time

        # Start timer
        isolated_metrics.start_processing_timer("test-1")

        # Simulate work
        time.sleep(0.01)  # 10ms

        # Stop timer
        latency = isolated_metrics.stop_processing_timer("test-1")

        # Latency should be around 10ms
        assert latency is not None
        assert latency >= 10  # At least 10ms

        # Check histogram has observation
        metrics_text = isolated_metrics.get_metrics_text()
        assert "mlsdm_processing_latency_milliseconds_count 1" in metrics_text


class TestPrometheusExportFormat:
    """Tests for Prometheus text format export."""

    def test_export_contains_help_and_type(self, isolated_metrics):
        """Test that export contains HELP and TYPE annotations."""
        metrics_text = isolated_metrics.get_metrics_text()

        # Should have HELP lines
        assert "# HELP mlsdm_" in metrics_text

        # Should have TYPE lines
        assert "# TYPE mlsdm_" in metrics_text

    def test_export_contains_all_registered_metrics(self, isolated_metrics):
        """Test that all registered metrics appear in export."""
        metrics_text = isolated_metrics.get_metrics_text()

        # Core counters
        expected_metrics = [
            "mlsdm_events_processed_total",
            "mlsdm_events_rejected_total",
            "mlsdm_errors_total",
            "mlsdm_moral_rejections_total",
            "mlsdm_requests_total",
            "mlsdm_emergency_shutdowns_total",
        ]

        for metric in expected_metrics:
            assert metric in metrics_text, f"Missing metric: {metric}"

    def test_export_bytes_matches_text(self, isolated_metrics):
        """Test that export_metrics() and get_metrics_text() are consistent."""
        bytes_output = isolated_metrics.export_metrics()
        text_output = isolated_metrics.get_metrics_text()

        assert bytes_output.decode("utf-8") == text_output

    def test_get_current_values_dictionary(self, isolated_metrics):
        """Test get_current_values returns correct dictionary."""
        isolated_metrics.increment_events_processed(10)
        isolated_metrics.set_phase("wake")
        isolated_metrics.set_moral_threshold(0.7)

        values = isolated_metrics.get_current_values()

        assert values["events_processed"] == 10
        assert values["phase"] == 1.0  # wake = 1
        assert values["moral_threshold"] == 0.7


class TestMetricsRegistryIntegration:
    """Tests for MetricsRegistry used in NeuroCognitiveEngine."""

    def test_request_tracking_with_provider(self, isolated_registry):
        """Test request tracking with provider labels."""
        # Simulate requests to different providers
        isolated_registry.increment_requests_total(provider_id="openai")
        isolated_registry.increment_requests_total(provider_id="openai")
        isolated_registry.increment_requests_total(provider_id="anthropic")

        snapshot = isolated_registry.get_snapshot()

        assert snapshot["requests_total"] == 3
        assert snapshot["requests_by_provider"]["openai"] == 2
        assert snapshot["requests_by_provider"]["anthropic"] == 1

    def test_latency_tracking(self, isolated_registry):
        """Test latency recording and summary statistics."""
        # Record latencies
        for lat in [10, 20, 30, 40, 50]:
            isolated_registry.record_latency_total(float(lat))

        summary = isolated_registry.get_summary()
        stats = summary["latency_stats"]["total_ms"]

        assert stats["count"] == 5
        assert stats["min"] == 10.0
        assert stats["max"] == 50.0
        assert stats["mean"] == 30.0

    def test_rejection_tracking_by_stage(self, isolated_registry):
        """Test rejection tracking by pipeline stage."""
        isolated_registry.increment_rejections_total("pre_flight")
        isolated_registry.increment_rejections_total("generation")
        isolated_registry.increment_rejections_total("pre_flight")
        isolated_registry.increment_rejections_total("post_moral")

        snapshot = isolated_registry.get_snapshot()

        assert snapshot["rejections_total"]["pre_flight"] == 2
        assert snapshot["rejections_total"]["generation"] == 1
        assert snapshot["rejections_total"]["post_moral"] == 1

    def test_error_tracking_by_type(self, isolated_registry):
        """Test error tracking by type."""
        isolated_registry.increment_errors_total("moral_precheck")
        isolated_registry.increment_errors_total("llm_timeout")
        isolated_registry.increment_errors_total("moral_precheck")

        snapshot = isolated_registry.get_snapshot()

        assert snapshot["errors_total"]["moral_precheck"] == 2
        assert snapshot["errors_total"]["llm_timeout"] == 1

    def test_reset_clears_all_metrics(self, isolated_registry):
        """Test that reset clears all metric values."""
        # Record some data
        isolated_registry.increment_requests_total()
        isolated_registry.increment_rejections_total("test")
        isolated_registry.record_latency_total(100.0)

        # Reset
        isolated_registry.reset()

        snapshot = isolated_registry.get_snapshot()

        assert snapshot["requests_total"] == 0
        assert snapshot["rejections_total"] == {}
        assert snapshot["latency_total_ms"] == []


class TestMetricsAfterSimulatedPipeline:
    """Tests that verify metrics after simulating full pipeline operations."""

    def test_successful_request_metrics(self, isolated_metrics):
        """Test metrics after successful request."""
        # Simulate successful request flow
        isolated_metrics.set_phase("wake")
        isolated_metrics.increment_events_processed()
        isolated_metrics.observe_generation_latency(150.0)
        isolated_metrics.observe_request_latency_seconds(0.15, "/generate", "wake")
        isolated_metrics.increment_requests("/generate", "2xx")

        # Verify all metrics updated
        assert isolated_metrics.events_processed._value.get() == 1
        assert isolated_metrics.phase_gauge._value.get() == 1.0

        metrics_text = isolated_metrics.get_metrics_text()
        assert "mlsdm_events_processed_total 1" in metrics_text
        assert 'mlsdm_requests_total{endpoint="/generate",status="2xx"} 1' in metrics_text

    def test_rejected_request_metrics(self, isolated_metrics):
        """Test metrics after rejected request."""
        # Simulate rejected request
        isolated_metrics.increment_events_rejected()
        isolated_metrics.increment_moral_rejection("below_threshold")
        isolated_metrics.increment_requests("/generate", "4xx")

        # Verify rejection metrics
        assert isolated_metrics.events_rejected._value.get() == 1
        assert isolated_metrics.moral_rejections.labels(
            reason="below_threshold"
        )._value.get() == 1

    def test_aphasia_pipeline_metrics(self, isolated_metrics):
        """Test metrics for aphasia detection and repair pipeline."""
        # Simulate aphasia detection
        severity = 0.65
        bucket = isolated_metrics.get_severity_bucket(severity)

        isolated_metrics.increment_aphasia_detected(bucket)
        isolated_metrics.increment_aphasia_repaired()

        # Verify
        assert isolated_metrics.aphasia_detected_total.labels(
            severity_bucket="high"
        )._value.get() == 1
        assert isolated_metrics.aphasia_repaired_total._value.get() == 1

    def test_emergency_shutdown_metrics(self, isolated_metrics):
        """Test metrics during emergency shutdown."""
        # Simulate emergency shutdown
        isolated_metrics.increment_emergency_shutdown("memory_exceeded")
        isolated_metrics.set_emergency_shutdown_active(True)

        # Verify
        shutdown_count = isolated_metrics.emergency_shutdowns.labels(
            reason="memory_exceeded"
        )._value.get()
        assert shutdown_count == 1
        assert isolated_metrics.emergency_shutdown_active._value.get() == 1.0

        # Reset shutdown
        isolated_metrics.set_emergency_shutdown_active(False)
        assert isolated_metrics.emergency_shutdown_active._value.get() == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
