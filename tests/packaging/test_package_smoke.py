"""
Smoke tests for MLSDM package verification.

These tests verify that the package is correctly installed and
core functionality works.

Run with:
    pytest tests/packaging/test_package_smoke.py -v
"""

import pytest


class TestPackageSmoke:
    """Smoke tests for package installation verification."""

    def test_package_import(self):
        """Test that mlsdm package can be imported."""
        import mlsdm

        assert mlsdm is not None
        assert hasattr(mlsdm, "__version__")

    def test_version_format(self):
        """Test that version follows semver format."""
        from mlsdm import __version__

        parts = __version__.split(".")
        assert len(parts) >= 2, f"Version should have at least major.minor: {__version__}"
        assert all(
            part.isdigit() or part.replace("-", "").replace("rc", "").isdigit()
            for part in parts[:2]
        ), f"Version parts should be numeric: {__version__}"

    def test_core_imports(self):
        """Test that core classes can be imported."""
        from mlsdm import (
            LLMWrapper,
            LLMPipeline,
            NeuroCognitiveEngine,
            NeuroCognitiveClient,
        )

        assert LLMWrapper is not None
        assert LLMPipeline is not None
        assert NeuroCognitiveEngine is not None
        assert NeuroCognitiveClient is not None

    def test_factory_functions(self):
        """Test that factory functions can be imported."""
        from mlsdm import (
            create_llm_wrapper,
            create_neuro_engine,
            create_llm_pipeline,
            build_neuro_engine_from_env,
        )

        assert callable(create_llm_wrapper)
        assert callable(create_neuro_engine)
        assert callable(create_llm_pipeline)
        assert callable(build_neuro_engine_from_env)

    def test_create_llm_wrapper_smoke(self):
        """Test that LLMWrapper can be created with defaults."""
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()
        assert wrapper is not None

    def test_llm_wrapper_generate(self):
        """Test that LLMWrapper can generate a response."""
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()
        result = wrapper.generate(prompt="Hello", moral_value=0.8)

        assert isinstance(result, dict)
        assert "response" in result
        assert "accepted" in result
        assert "phase" in result
        assert result["accepted"] is True  # 0.8 > 0.5 default threshold

    def test_llm_wrapper_state(self):
        """Test that LLMWrapper state can be retrieved."""
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()
        state = wrapper.get_state()

        assert isinstance(state, dict)
        assert "phase" in state
        assert "step" in state
        assert "moral_threshold" in state

    def test_create_neuro_engine_smoke(self):
        """Test that NeuroCognitiveEngine can be created."""
        from mlsdm import create_neuro_engine

        engine = create_neuro_engine()
        assert engine is not None

    def test_neuro_engine_generate(self):
        """Test that NeuroCognitiveEngine can generate a response."""
        from mlsdm import create_neuro_engine

        engine = create_neuro_engine()
        result = engine.generate(prompt="Test", moral_value=0.8)

        assert isinstance(result, dict)
        assert "response" in result

    def test_create_llm_pipeline_smoke(self):
        """Test that LLMPipeline can be created."""
        from mlsdm import create_llm_pipeline

        pipeline = create_llm_pipeline()
        assert pipeline is not None

    def test_neuro_cognitive_client_smoke(self):
        """Test that NeuroCognitiveClient can be created."""
        from mlsdm import NeuroCognitiveClient

        client = NeuroCognitiveClient(backend="local_stub")
        assert client is not None

    def test_client_generate(self):
        """Test that NeuroCognitiveClient can generate a response."""
        from mlsdm import NeuroCognitiveClient

        client = NeuroCognitiveClient(backend="local_stub")
        result = client.generate(prompt="Hello", moral_value=0.8)

        assert isinstance(result, dict)
        assert "response" in result


class TestCLISmoke:
    """Smoke tests for CLI."""

    def test_cli_import(self):
        """Test that CLI can be imported."""
        from mlsdm.cli import main

        assert callable(main)

    def test_cli_info_command(self):
        """Test that info command works."""
        from mlsdm.cli import cmd_info
        import argparse

        args = argparse.Namespace()
        result = cmd_info(args)
        assert result == 0

    def test_cli_check_command(self):
        """Test that check command works."""
        from mlsdm.cli import cmd_check
        import argparse

        args = argparse.Namespace(verbose=False)
        result = cmd_check(args)
        assert result == 0


class TestAPISmoke:
    """Smoke tests for API components."""

    def test_api_app_import(self):
        """Test that API app can be imported."""
        from mlsdm.api.app import app

        assert app is not None

    def test_api_health_router_import(self):
        """Test that health router can be imported."""
        from mlsdm.api.health import router

        assert router is not None

    def test_fastapi_app_has_routes(self):
        """Test that FastAPI app has expected routes."""
        from mlsdm.api.app import app

        routes = [r.path for r in app.routes]
        assert "/health" in routes or any("/health" in r for r in routes)
        assert "/generate" in routes
        assert "/infer" in routes


class TestObservabilitySmoke:
    """Smoke tests for observability components."""

    def test_metrics_exporter_import(self):
        """Test that metrics exporter can be imported."""
        from mlsdm.observability.metrics import get_metrics_exporter

        exporter = get_metrics_exporter()
        assert exporter is not None

    def test_metrics_text_output(self):
        """Test that metrics can be exported as text."""
        from mlsdm.observability.metrics import get_metrics_exporter

        exporter = get_metrics_exporter()
        text = exporter.get_metrics_text()
        assert isinstance(text, str)
