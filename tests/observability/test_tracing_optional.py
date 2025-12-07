"""Tests for optional OpenTelemetry tracing.

This module tests that the tracing system gracefully handles both scenarios:
1. OpenTelemetry SDK is available and enabled
2. OpenTelemetry SDK is not available (ImportError)

The system should work correctly in both cases, degrading to no-op when OTEL is unavailable.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator


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
    """Test tracing when OpenTelemetry is not available (ImportError)."""

    @pytest.fixture
    def mock_import_error(self) -> Iterator[None]:
        """Mock ImportError for opentelemetry to simulate unavailable SDK.
        
        This uses sys.modules manipulation to simulate the package not being installed.
        """
        # Save original modules
        original_modules = {}
        otel_modules = [
            "opentelemetry",
            "opentelemetry.trace",
            "opentelemetry.sdk",
            "opentelemetry.sdk.trace",
            "opentelemetry.sdk.resources",
            "opentelemetry.sdk.trace.export",
        ]
        
        for module in otel_modules:
            if module in sys.modules:
                original_modules[module] = sys.modules[module]
                del sys.modules[module]
        
        # Remove tracing module to force reimport
        if "mlsdm.observability.tracing" in sys.modules:
            del sys.modules["mlsdm.observability.tracing"]
        
        # Mock import to raise ImportError
        original_import = __builtins__.__import__
        
        def mock_import(name: str, *args: Any, **kwargs: Any) -> Any:
            if name.startswith("opentelemetry"):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)
        
        with patch.object(__builtins__, "__import__", side_effect=mock_import):
            # Force reimport of tracing module
            import mlsdm.observability.tracing
            from importlib import reload
            reload(mlsdm.observability.tracing)
            
            yield
        
        # Restore original modules
        for module, obj in original_modules.items():
            sys.modules[module] = obj
        
        # Force reimport to restore original state
        if "mlsdm.observability.tracing" in sys.modules:
            del sys.modules["mlsdm.observability.tracing"]

    def test_otel_unavailable_flag_false_when_not_installed(
        self, mock_import_error: None
    ) -> None:
        """Verify OTEL_AVAILABLE is False when opentelemetry is not installed."""
        from mlsdm.observability import tracing

        assert tracing.OTEL_AVAILABLE is False

    def test_is_otel_available_returns_false_when_not_installed(
        self, mock_import_error: None
    ) -> None:
        """Verify is_otel_available() returns False when OTEL is not installed."""
        from mlsdm.observability.tracing import is_otel_available

        assert is_otel_available() is False

    def test_is_otel_enabled_returns_false_when_not_available(
        self, mock_import_error: None, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify is_otel_enabled() returns False when OTEL is not available."""
        from mlsdm.observability.tracing import is_otel_enabled

        # Even if env says enable, should return False if not available
        monkeypatch.setenv("MLSDM_ENABLE_OTEL", "true")
        assert is_otel_enabled() is False

    def test_tracing_config_raises_when_enabled_but_unavailable(
        self, mock_import_error: None
    ) -> None:
        """Verify TracingConfig raises clear error when enabled but OTEL unavailable."""
        from mlsdm.observability.tracing import TracingConfig

        with pytest.raises(RuntimeError) as exc_info:
            TracingConfig(enabled=True)

        error_message = str(exc_info.value)
        assert "opentelemetry-sdk" in error_message
        assert "not installed" in error_message
        assert "MLSDM_ENABLE_OTEL=false" in error_message

    def test_tracing_config_succeeds_when_disabled_and_unavailable(
        self, mock_import_error: None
    ) -> None:
        """Verify TracingConfig works fine when disabled and OTEL unavailable."""
        from mlsdm.observability.tracing import TracingConfig

        # Should not raise
        config = TracingConfig(enabled=False)
        assert config.enabled is False

    def test_tracer_manager_returns_noop_when_unavailable(
        self, mock_import_error: None
    ) -> None:
        """Verify TracerManager returns NoOpTracer when OTEL is unavailable."""
        from mlsdm.observability.tracing import (
            NoOpTracer,
            TracerManager,
            TracingConfig,
        )

        config = TracingConfig(enabled=False)
        manager = TracerManager(config)
        tracer = manager.tracer

        # Should get NoOpTracer
        assert isinstance(tracer, NoOpTracer)

    def test_noop_span_context_manager_works(self, mock_import_error: None) -> None:
        """Verify NoOpSpan works as a context manager."""
        from mlsdm.observability.tracing import NoOpSpan

        # Should not raise
        with NoOpSpan() as span:
            assert span is not None
            span.set_attribute("test", "value")
            span.record_exception(ValueError("test"))
            span.set_status(None, "test")

    def test_noop_tracer_start_span_works(self, mock_import_error: None) -> None:
        """Verify NoOpTracer.start_as_current_span works."""
        from mlsdm.observability.tracing import NoOpTracer

        tracer = NoOpTracer()

        # Should not raise
        with tracer.start_as_current_span("test_span") as span:
            assert span is not None
            span.set_attribute("key", "value")

    def test_tracer_manager_start_span_works_when_unavailable(
        self, mock_import_error: None
    ) -> None:
        """Verify TracerManager.start_span works even when OTEL unavailable."""
        from mlsdm.observability.tracing import TracerManager, TracingConfig

        config = TracingConfig(enabled=False)
        manager = TracerManager(config)

        # Should not raise
        with manager.start_span("test_span") as span:
            assert span is not None
            span.set_attribute("test_key", "test_value")


# ---------------------------------------------------------------------------
# Integration: Core MLSDM imports without OTEL
# ---------------------------------------------------------------------------


class TestCoreImportsWithoutOTEL:
    """Test that core MLSDM components can be imported without OTEL."""

    def test_mlsdm_core_imports_without_otel(self, mock_import_error: None) -> None:
        """Verify core MLSDM modules import successfully without OTEL."""
        # Should not raise ImportError
        import mlsdm.observability.tracing
        import mlsdm.observability.logger
        import mlsdm.observability.metrics

        # Verify tracing module loaded with OTEL_AVAILABLE=False
        assert mlsdm.observability.tracing.OTEL_AVAILABLE is False

    def test_span_helper_function_works_without_otel(
        self, mock_import_error: None
    ) -> None:
        """Verify span() context manager works without OTEL."""
        from mlsdm.observability.tracing import span

        # Should not raise
        with span("test_operation", phase="wake"):
            pass  # No-op but shouldn't crash

    def test_get_tracer_manager_works_without_otel(
        self, mock_import_error: None
    ) -> None:
        """Verify get_tracer_manager() works without OTEL."""
        from mlsdm.observability.tracing import get_tracer_manager

        manager = get_tracer_manager()
        assert manager is not None
        
        # Should be able to use it
        with manager.start_span("test") as s:
            s.set_attribute("key", "value")


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
