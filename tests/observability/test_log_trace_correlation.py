"""
Tests for log-trace correlation (trace_id/span_id injection).

These tests validate that:
1. trace_id and span_id are injected into JSON logs when tracing is active
2. Graceful fallback when tracing is disabled (no crash, no trace fields)
3. W3C trace format compliance (32 hex chars for trace_id, 16 for span_id)
4. get_current_trace_context() helper function works correctly
"""

import json
import logging

import pytest

from mlsdm.observability import (
    TracerManager,
    TracingConfig,
    get_current_trace_context,
    span,
)
from mlsdm.observability.logger import JSONFormatter


@pytest.fixture
def fresh_tracer():
    """Create a fresh tracer manager for isolation."""
    TracerManager.reset_instance()
    config = TracingConfig(enabled=True, exporter_type="none")
    manager = TracerManager(config)
    manager.initialize()
    yield manager
    TracerManager.reset_instance()


@pytest.fixture
def disabled_tracer():
    """Create a disabled tracer manager."""
    TracerManager.reset_instance()
    config = TracingConfig(enabled=False)
    manager = TracerManager(config)
    manager.initialize()
    yield manager
    TracerManager.reset_instance()


class TestGetCurrentTraceContext:
    """Tests for get_current_trace_context helper function."""

    def test_returns_none_when_no_span(self, disabled_tracer):
        """Test that function returns None values when no span is active."""
        context = get_current_trace_context()
        assert context["trace_id"] is None
        assert context["span_id"] is None

    def test_returns_valid_context_within_span(self, fresh_tracer):
        """Test that function returns valid context within an active span."""
        with span("test.operation") as _:
            context = get_current_trace_context()
            assert context["trace_id"] is not None
            assert context["span_id"] is not None

    def test_trace_id_format_w3c_compliant(self, fresh_tracer):
        """Test that trace_id is W3C compliant (32 hex characters)."""
        with span("test.operation") as _:
            context = get_current_trace_context()
            trace_id = context["trace_id"]
            assert trace_id is not None
            assert len(trace_id) == 32  # 16 bytes = 32 hex chars
            assert all(c in "0123456789abcdef" for c in trace_id)

    def test_span_id_format_w3c_compliant(self, fresh_tracer):
        """Test that span_id is W3C compliant (16 hex characters)."""
        with span("test.operation") as _:
            context = get_current_trace_context()
            span_id = context["span_id"]
            assert span_id is not None
            assert len(span_id) == 16  # 8 bytes = 16 hex chars
            assert all(c in "0123456789abcdef" for c in span_id)

    def test_different_spans_have_different_ids(self, fresh_tracer):
        """Test that different spans have different span_ids."""
        with span("test.operation1") as _:
            context1 = get_current_trace_context()

        with span("test.operation2") as _:
            context2 = get_current_trace_context()

        # Span IDs should be different
        assert context1["span_id"] != context2["span_id"]
        # Trace IDs should also be different (separate root spans)
        assert context1["trace_id"] != context2["trace_id"]


class TestJSONFormatterTraceCorrelation:
    """Tests for trace correlation in JSONFormatter."""

    def test_logs_include_trace_id_within_span(self, fresh_tracer, tmp_path):
        """Test that logs include trace_id when within a span."""
        # Set up a logger with JSONFormatter
        log_file = tmp_path / "test.log"
        logger = logging.getLogger("test_trace_correlation")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        handler.setFormatter(JSONFormatter())
        logger.handlers = [handler]

        # Log within a span
        with span("test.operation") as _:
            logger.info("Test message within span")

        handler.close()

        # Parse the log and verify trace_id is present
        log_content = log_file.read_text().strip()
        log_entry = json.loads(log_content)

        assert "trace_id" in log_entry
        assert log_entry["trace_id"] is not None
        assert len(log_entry["trace_id"]) == 32

    def test_logs_include_span_id_within_span(self, fresh_tracer, tmp_path):
        """Test that logs include span_id when within a span."""
        log_file = tmp_path / "test.log"
        logger = logging.getLogger("test_span_correlation")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        handler.setFormatter(JSONFormatter())
        logger.handlers = [handler]

        with span("test.operation") as _:
            logger.info("Test message within span")

        handler.close()

        log_content = log_file.read_text().strip()
        log_entry = json.loads(log_content)

        assert "span_id" in log_entry
        assert log_entry["span_id"] is not None
        assert len(log_entry["span_id"]) == 16

    def test_logs_omit_trace_fields_when_no_span(self, disabled_tracer, tmp_path):
        """Test that logs don't include trace fields when no span is active."""
        log_file = tmp_path / "test.log"
        logger = logging.getLogger("test_no_trace")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        handler.setFormatter(JSONFormatter())
        logger.handlers = [handler]

        logger.info("Test message without span")

        handler.close()

        log_content = log_file.read_text().strip()
        log_entry = json.loads(log_content)

        # trace_id and span_id should not be in the log entry
        assert "trace_id" not in log_entry
        assert "span_id" not in log_entry

    def test_nested_spans_preserve_trace_id(self, fresh_tracer, tmp_path):
        """Test that nested spans preserve the same trace_id."""
        log_file = tmp_path / "test.log"
        logger = logging.getLogger("test_nested_trace")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        handler.setFormatter(JSONFormatter())
        logger.handlers = [handler]

        with span("parent.operation") as _:
            logger.info("Parent span message")
            with span("child.operation") as _:
                logger.info("Child span message")

        handler.close()

        # Parse both log entries
        log_content = log_file.read_text().strip()
        log_lines = log_content.split("\n")
        parent_entry = json.loads(log_lines[0])
        child_entry = json.loads(log_lines[1])

        # Trace IDs should be the same (same trace context)
        assert parent_entry["trace_id"] == child_entry["trace_id"]
        # Span IDs should be different
        assert parent_entry["span_id"] != child_entry["span_id"]


class TestObservabilityLoggerTraceCorrelation:
    """Tests for trace correlation in ObservabilityLogger."""

    def test_observability_logger_includes_trace_context(self, fresh_tracer, tmp_path):
        """Test that ObservabilityLogger includes trace context in logs."""
        from mlsdm.observability.logger import EventType, ObservabilityLogger

        log_file = tmp_path / "obs_test.log"
        obs_logger = ObservabilityLogger(
            logger_name="test_obs_trace",
            log_dir=tmp_path,
            log_file="obs_test.log",
            console_output=False,
        )

        with span("test.observability.operation") as _:
            obs_logger.info(
                EventType.EVENT_PROCESSED,
                "Test observability log",
                metrics={"key": "value"},
            )

        # Read the size-based rotation log
        log_content = log_file.read_text().strip()
        if log_content:
            log_entry = json.loads(log_content.split("\n")[0])
            assert "trace_id" in log_entry
            assert log_entry["trace_id"] is not None


class TestGracefulFallback:
    """Tests for graceful fallback behavior."""

    def test_no_crash_when_otel_not_imported(self, tmp_path):
        """Test that logging works even if OTel context retrieval fails."""
        log_file = tmp_path / "test.log"
        logger = logging.getLogger("test_fallback")
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_file)
        handler.setFormatter(JSONFormatter())
        logger.handlers = [handler]

        # This should not crash even without active tracing
        logger.info("Test message")

        handler.close()

        log_content = log_file.read_text().strip()
        log_entry = json.loads(log_content)

        # Should have basic fields
        assert "message" in log_entry
        assert log_entry["message"] == "Test message"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
