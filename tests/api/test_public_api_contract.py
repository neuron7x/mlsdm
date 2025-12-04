"""
Public API Contract Tests.

These tests verify that the minimal public API surface is stable and working.
The public API is defined in `mlsdm/__init__.py` and consists of:

1. NeuroCognitiveClient - SDK client for generating governed responses
2. create_llm_wrapper - Factory for creating LLMWrapper instances
3. create_neuro_engine - Factory for creating NeuroCognitiveEngine instances
4. __version__ - Package version string

CONTRACT STABILITY:
These tests protect the public API contract. If a test fails after code changes,
it indicates a potential breaking change to the public interface.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment for public API tests."""
    os.environ["DISABLE_RATE_LIMIT"] = "1"
    os.environ["LLM_BACKEND"] = "local_stub"
    yield
    if "DISABLE_RATE_LIMIT" in os.environ:
        del os.environ["DISABLE_RATE_LIMIT"]


class TestPublicAPIExports:
    """Test that public API exports are available and stable."""

    def test_public_api_exports_from_mlsdm(self):
        """Test that __all__ exports the minimal public API."""
        from mlsdm import __all__

        # Expected minimal public API
        expected = {
            "__version__",
            "NeuroCognitiveClient",
            "create_llm_wrapper",
            "create_neuro_engine",
        }

        assert set(__all__) == expected, (
            f"Public API should be minimal. Expected: {expected}, Got: {set(__all__)}"
        )

    def test_version_is_string(self):
        """Test that __version__ is a valid version string."""
        from mlsdm import __version__

        assert isinstance(__version__, str)
        # Should be semver-like (major.minor.patch)
        parts = __version__.split(".")
        assert len(parts) >= 2, f"Version should be semver format: {__version__}"

    def test_neuroCognitiveClient_importable(self):
        """Test that NeuroCognitiveClient is importable."""
        from mlsdm import NeuroCognitiveClient

        assert NeuroCognitiveClient is not None
        assert callable(NeuroCognitiveClient)

    def test_create_llm_wrapper_importable(self):
        """Test that create_llm_wrapper factory is importable."""
        from mlsdm import create_llm_wrapper

        assert create_llm_wrapper is not None
        assert callable(create_llm_wrapper)

    def test_create_neuro_engine_importable(self):
        """Test that create_neuro_engine factory is importable."""
        from mlsdm import create_neuro_engine

        assert create_neuro_engine is not None
        assert callable(create_neuro_engine)


class TestNeuroCognitiveClientContract:
    """Test NeuroCognitiveClient public interface contract."""

    def test_client_instantiation_with_local_stub(self):
        """Test client can be instantiated with local_stub backend."""
        from mlsdm import NeuroCognitiveClient

        client = NeuroCognitiveClient(backend="local_stub")
        assert client is not None
        assert client.backend == "local_stub"

    def test_client_generate_returns_dict(self):
        """Test generate() returns a dictionary with required fields."""
        from mlsdm import NeuroCognitiveClient

        client = NeuroCognitiveClient(backend="local_stub")
        result = client.generate("Hello, world!")

        assert isinstance(result, dict)
        # Core response fields
        assert "response" in result
        assert isinstance(result["response"], str)

    def test_client_generate_with_parameters(self):
        """Test generate() accepts optional parameters."""
        from mlsdm import NeuroCognitiveClient

        client = NeuroCognitiveClient(backend="local_stub")
        result = client.generate(
            "Test prompt",
            max_tokens=100,
            moral_value=0.8,
        )

        assert isinstance(result, dict)
        assert "response" in result

    def test_client_has_backend_property(self):
        """Test client exposes backend property."""
        from mlsdm import NeuroCognitiveClient

        client = NeuroCognitiveClient(backend="local_stub")
        assert hasattr(client, "backend")
        assert client.backend == "local_stub"


class TestCreateLLMWrapperContract:
    """Test create_llm_wrapper factory interface contract."""

    def test_create_llm_wrapper_default_parameters(self):
        """Test create_llm_wrapper works with defaults."""
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()
        assert wrapper is not None

    def test_wrapper_has_generate_method(self):
        """Test wrapper has generate() method."""
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()
        assert hasattr(wrapper, "generate")
        assert callable(wrapper.generate)

    def test_wrapper_generate_returns_dict(self):
        """Test wrapper.generate() returns dictionary."""
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()
        result = wrapper.generate(prompt="Hello", moral_value=0.8)

        assert isinstance(result, dict)
        # Required contract fields
        assert "response" in result
        assert "accepted" in result
        assert "phase" in result

    def test_wrapper_generate_response_structure(self):
        """Test wrapper.generate() returns expected structure."""
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()
        result = wrapper.generate(prompt="Test", moral_value=0.9)

        # Core fields that must be present
        assert "response" in result
        assert "accepted" in result
        assert "phase" in result
        assert "note" in result

        # Type checks
        assert isinstance(result["response"], str)
        assert isinstance(result["accepted"], bool)
        assert isinstance(result["phase"], str)
        assert result["phase"] in ["wake", "sleep"]

    def test_wrapper_has_get_state_method(self):
        """Test wrapper has get_state() method."""
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()
        assert hasattr(wrapper, "get_state")
        assert callable(wrapper.get_state)

    def test_wrapper_get_state_returns_dict(self):
        """Test wrapper.get_state() returns dictionary."""
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()
        state = wrapper.get_state()

        assert isinstance(state, dict)
        # Expected state fields
        assert "phase" in state
        assert "step" in state


class TestCreateNeuroEngineContract:
    """Test create_neuro_engine factory interface contract."""

    def test_create_neuro_engine_default_parameters(self):
        """Test create_neuro_engine works with defaults."""
        from mlsdm import create_neuro_engine

        engine = create_neuro_engine()
        assert engine is not None

    def test_engine_has_generate_method(self):
        """Test engine has generate() method."""
        from mlsdm import create_neuro_engine

        engine = create_neuro_engine()
        assert hasattr(engine, "generate")
        assert callable(engine.generate)

    def test_engine_generate_returns_dict(self):
        """Test engine.generate() returns dictionary."""
        from mlsdm import create_neuro_engine

        engine = create_neuro_engine()
        result = engine.generate("Hello, world!")

        assert isinstance(result, dict)
        assert "response" in result

    def test_engine_generate_response_structure(self):
        """Test engine.generate() returns expected structure."""
        from mlsdm import create_neuro_engine

        engine = create_neuro_engine()
        result = engine.generate("Test prompt")

        # Core fields
        assert "response" in result
        assert isinstance(result["response"], str)

        # Should have timing and validation info
        assert "timing" in result or "mlsdm" in result


class TestExtendedAPIBackwardCompatibility:
    """Test that extended API is still accessible for backward compatibility."""

    def test_llm_wrapper_importable(self):
        """Test LLMWrapper is still importable from mlsdm."""
        from mlsdm import LLMWrapper

        assert LLMWrapper is not None

    def test_neuro_cognitive_engine_importable(self):
        """Test NeuroCognitiveEngine is still importable."""
        from mlsdm import NeuroCognitiveEngine

        assert NeuroCognitiveEngine is not None

    def test_llm_pipeline_importable(self):
        """Test LLMPipeline is still importable."""
        from mlsdm import LLMPipeline

        assert LLMPipeline is not None

    def test_speech_governance_importable(self):
        """Test speech governance components are still importable."""
        from mlsdm import SpeechGovernor, SpeechGovernanceResult

        assert SpeechGovernor is not None
        assert SpeechGovernanceResult is not None

    def test_config_types_importable(self):
        """Test configuration types are still importable."""
        from mlsdm import NeuroEngineConfig, PipelineConfig

        assert NeuroEngineConfig is not None
        assert PipelineConfig is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
