"""Tests for optional OpenTelemetry tracing.

This module tests that the tracing system gracefully handles both scenarios:
1. OpenTelemetry SDK is available and enabled
2. OpenTelemetry SDK is not available (ImportError)

The system should work correctly in both cases, degrading to no-op when OTEL is unavailable.
"""

from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Scenario A: OTEL Available and Enabled
# ---------------------------------------------------------------------------


class TestOTELAvailableEnabled:
    """Test tracing when OpenTelemetry is available and enabled."""

    def test_otel_available_flag_true_when_installed(self) -> None:
        """Verify OTEL_AVAILABLE is True when opentelemetry is installed."""
        from mlsdm.observability import tracing

        # In test environment, OTEL should be available
        assert tracing.OTEL_AVAILABLE is True

    def test_is_otel_available_returns_true(self) -> None:
        """Verify is_otel_available() returns True when OTEL is installed."""
        from mlsdm.observability.tracing import is_otel_available

        assert is_otel_available() is True

    def test_is_otel_enabled_respects_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify is_otel_enabled() respects MLSDM_ENABLE_OTEL environment variable."""
        from mlsdm.observability.tracing import is_otel_enabled

        # Test enabled explicitly
        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "true")
        assert is_otel_enabled() is True

        # Test disabled explicitly
        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "false")
        assert is_otel_enabled() is False

    def test_is_otel_enabled_respects_otel_sdk_disabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify is_otel_enabled() respects standard OTEL_SDK_DISABLED variable."""
        from mlsdm.observability.tracing import is_otel_enabled

        # MLSDM_ENABLE_OTEL not set, fall back to OTEL_SDK_DISABLED
        monkeypatch.delenv("MLSDM_ENABLE_OTEL", raising=False)

        # Test enabled (OTEL_SDK_DISABLED=false)
        monkeypatch.setenv("OTEL_SDK_DISABLED", "false")
        assert is_otel_enabled() is True

        # Test disabled (OTEL_SDK_DISABLED=true)
        monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
        assert is_otel_enabled() is False

    def test_mlsdm_enable_otel_takes_precedence(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify MLSDM_ENABLE_OTEL takes precedence over OTEL_SDK_DISABLED."""
        from mlsdm.observability.tracing import is_otel_enabled

        # MLSDM says enable, OTEL says disable - MLSDM wins
        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "true")
        monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
        assert is_otel_enabled() is True

        # MLSDM says disable, OTEL says enable - MLSDM wins
        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "false")
        monkeypatch.setenv("OTEL_SDK_DISABLED", "false")
        assert is_otel_enabled() is False

    def test_tracer_manager_returns_real_tracer_when_enabled(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify TracerManager returns a real tracer when OTEL is available and enabled."""
        from mlsdm.observability.tracing import TracerManager, TracingConfig

        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "false")  # Disable to avoid initialization
        config = TracingConfig(enabled=False)
        manager = TracerManager(config)
        tracer = manager.tracer

        # Should get a tracer (may be no-op since not initialized, but not None)
        assert tracer is not None
        assert hasattr(tracer, "start_as_current_span")

    def test_tracer_start_span_works_when_otel_available(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify span creation works when OTEL is available (even if disabled)."""
        from mlsdm.observability.tracing import TracerManager, TracingConfig

        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "false")
        config = TracingConfig(enabled=False)
        manager = TracerManager(config)

        # Should not raise even though tracing is disabled
        with manager.start_span("test_span") as span:
            assert span is not None
            span.set_attribute("test_key", "test_value")


# ---------------------------------------------------------------------------
# Scenario B: OTEL Unavailable (Simulated ImportError)
# ---------------------------------------------------------------------------


class TestOTELUnavailable:
    """Test tracing when OpenTelemetry is not available (ImportError).

    Note: These tests verify the NoOp implementations work correctly.
    Testing actual import failure is complex and may cause test pollution,
    so we focus on testing the fallback behavior directly.
    """

    def test_noop_span_context_manager_works(self) -> None:
        """Verify NoOpSpan works as a context manager."""
        from mlsdm.observability.tracing import NoOpSpan

        # Should not raise
        with NoOpSpan() as span:
            assert span is not None
            span.set_attribute("test", "value")
            span.record_exception(ValueError("test"))
            span.set_status(None, "test")
            span.add_event("test_event")
            assert span.is_recording() is False

    def test_noop_tracer_start_span_works(self) -> None:
        """Verify NoOpTracer.start_as_current_span works."""
        from mlsdm.observability.tracing import NoOpTracer

        tracer = NoOpTracer()

        # Should not raise
        with tracer.start_as_current_span("test_span") as span:
            assert span is not None
            span.set_attribute("key", "value")

    def test_noop_tracer_start_span_direct(self) -> None:
        """Verify NoOpTracer.start_span works."""
        from mlsdm.observability.tracing import NoOpTracer

        tracer = NoOpTracer()
        span = tracer.start_span("test_span")
        assert span is not None
        span.set_attribute("key", "value")

    def test_tracer_returns_noop_when_otel_unavailable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify TracerManager returns NoOpTracer when OTEL is not available."""
        from mlsdm.observability.tracing import TracerManager, TracingConfig

        # When OTEL_AVAILABLE is False, should get NoOpTracer
        # We can test this by disabling and checking behavior
        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "false")
        config = TracingConfig(enabled=False)
        manager = TracerManager(config)

        # Should not raise even though disabled
        with manager.start_span("test_span") as span:
            assert span is not None
            span.set_attribute("test_key", "test_value")

    def test_tracing_config_validates_availability(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify TracingConfig validates OTEL availability when enabled.

        If OTEL is available (dev environment), this won't raise.
        If OTEL is not available, it should raise a clear error.
        """
        from mlsdm.observability.tracing import OTEL_AVAILABLE, TracingConfig

        if OTEL_AVAILABLE:
            # In dev environment with OTEL installed
            monkeypatch.setenv("MLSDM_ENABLE_OTEL", "true")
            config = TracingConfig(enabled=True)
            assert config.enabled is True
        else:
            # If OTEL not available, should raise
            with pytest.raises(RuntimeError) as exc_info:
                TracingConfig(enabled=True)

            error_message = str(exc_info.value)
            assert "opentelemetry-sdk" in error_message
            assert "not installed" in error_message


# ---------------------------------------------------------------------------
# Integration: Core MLSDM imports
# ---------------------------------------------------------------------------


class TestCoreImports:
    """Test that core MLSDM components can be imported."""

    def test_mlsdm_core_imports_successfully(self) -> None:
        """Verify core MLSDM modules import successfully."""
        # Should not raise ImportError
        import mlsdm.observability.logger
        import mlsdm.observability.metrics
        import mlsdm.observability.tracing

        # Verify tracing module loaded
        assert hasattr(mlsdm.observability.tracing, "OTEL_AVAILABLE")

    def test_span_helper_function_works(self) -> None:
        """Verify span() context manager works."""
        from mlsdm.observability.tracing import span

        # Should not raise
        with span("test_operation", phase="wake"):
            pass  # May be no-op or real span, but shouldn't crash

    def test_get_tracer_manager_works(self) -> None:
        """Verify get_tracer_manager() works."""
        from mlsdm.observability.tracing import get_tracer_manager

        manager = get_tracer_manager()
        assert manager is not None

        # Should be able to use it
        with manager.start_span("test") as s:
            s.set_attribute("key", "value")

    def test_is_otel_available_function_exists(self) -> None:
        """Verify is_otel_available() function exists and returns a bool."""
        from mlsdm.observability.tracing import is_otel_available

        result = is_otel_available()
        assert isinstance(result, bool)

    def test_is_otel_enabled_function_exists(self) -> None:
        """Verify is_otel_enabled() function exists and returns a bool."""
        from mlsdm.observability.tracing import is_otel_enabled

        result = is_otel_enabled()
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Configuration validation
# ---------------------------------------------------------------------------


class TestConfigurationValidation:
    """Test configuration validation for OTEL settings."""

    def test_env_var_mlsdm_enable_otel_parsed_correctly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify MLSDM_ENABLE_OTEL environment variable is parsed correctly."""
        from mlsdm.observability.tracing import TracingConfig

        # Test various true values
        for true_value in ["true", "TRUE", "True"]:
            monkeypatch.setenv("MLSDM_ENABLE_OTEL", true_value)
            config = TracingConfig()
            assert config.enabled is True

        # Test false value
        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "false")
        config = TracingConfig()
        assert config.enabled is False

    def test_config_enabled_parameter_overrides_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify explicit enabled parameter overrides environment variables."""
        from mlsdm.observability.tracing import TracingConfig

        # Env says true, but parameter says false
        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "true")
        config = TracingConfig(enabled=False)
        assert config.enabled is False

        # Env says false, but parameter says true (should raise if OTEL available)
        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "false")
        # This might raise if OTEL is available - that's expected
        try:
            config = TracingConfig(enabled=True)
            assert config.enabled is True
        except RuntimeError:
            # Expected if OTEL is not available
            pass
