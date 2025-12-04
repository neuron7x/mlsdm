"""
SDK Public Client API Contract Tests.

These tests verify the public SDK client interface contract.
The SDK provides NeuroCognitiveClient as the primary interface for users.

CONTRACT STABILITY:
These tests protect the SDK contract. If a test fails after code changes,
it indicates a potential breaking change that requires a major version bump.
"""

import os

import pytest


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment for SDK tests."""
    os.environ["DISABLE_RATE_LIMIT"] = "1"
    os.environ["LLM_BACKEND"] = "local_stub"
    yield
    if "DISABLE_RATE_LIMIT" in os.environ:
        del os.environ["DISABLE_RATE_LIMIT"]


class TestSDKImports:
    """Test that SDK imports work correctly."""

    def test_sdk_client_importable_from_mlsdm(self):
        """Test NeuroCognitiveClient importable from top-level."""
        from mlsdm import NeuroCognitiveClient

        assert NeuroCognitiveClient is not None

    def test_sdk_client_importable_from_sdk(self):
        """Test NeuroCognitiveClient importable from mlsdm.sdk."""
        from mlsdm.sdk import NeuroCognitiveClient

        assert NeuroCognitiveClient is not None

    def test_sdk_exceptions_importable(self):
        """Test SDK exception classes are importable."""
        from mlsdm.sdk import (
            MLSDMClientError,
            MLSDMError,
            MLSDMServerError,
            MLSDMTimeoutError,
        )

        assert issubclass(MLSDMClientError, MLSDMError)
        assert issubclass(MLSDMServerError, MLSDMError)
        assert issubclass(MLSDMTimeoutError, MLSDMError)

    def test_sdk_response_dto_importable(self):
        """Test response DTO classes are importable."""
        from mlsdm.sdk import CognitiveStateDTO, GenerateResponseDTO

        assert GenerateResponseDTO is not None
        assert CognitiveStateDTO is not None


class TestSDKClientInterface:
    """Test the SDK client public interface."""

    def test_client_init_with_local_stub(self):
        """Test client initialization with local_stub backend."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient(backend="local_stub")
        assert client.backend == "local_stub"

    def test_client_init_default_backend(self):
        """Test client uses local_stub by default."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        assert client.backend == "local_stub"

    def test_client_invalid_backend_raises_error(self):
        """Test client raises ValueError for invalid backend."""
        from mlsdm.sdk import NeuroCognitiveClient

        with pytest.raises(ValueError, match="Invalid backend"):
            NeuroCognitiveClient(backend="invalid_backend")

    def test_client_has_generate_method(self):
        """Test client has generate() method."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        assert hasattr(client, "generate")
        assert callable(client.generate)

    def test_client_has_generate_typed_method(self):
        """Test client has generate_typed() method."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        assert hasattr(client, "generate_typed")
        assert callable(client.generate_typed)

    def test_client_has_backend_property(self):
        """Test client has backend property."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        assert hasattr(client, "backend")

    def test_client_has_config_property(self):
        """Test client has config property."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        assert hasattr(client, "config")


class TestSDKGenerateMethod:
    """Test the generate() method contract."""

    def test_generate_accepts_prompt(self):
        """Test generate accepts prompt parameter."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        result = client.generate("Test prompt")
        assert isinstance(result, dict)

    def test_generate_accepts_optional_parameters(self):
        """Test generate accepts optional parameters."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        result = client.generate(
            "Test",
            max_tokens=100,
            moral_value=0.8,
            user_intent="conversational",
            cognitive_load=0.5,
            context_top_k=3,
        )
        assert isinstance(result, dict)

    def test_generate_response_has_required_fields(self):
        """Test generate returns dict with required fields."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        result = client.generate("Hello")

        assert "response" in result
        assert isinstance(result["response"], str)

    def test_generate_response_has_mlsdm_state(self):
        """Test generate returns mlsdm state."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        result = client.generate("Test")

        assert "mlsdm" in result
        assert isinstance(result["mlsdm"], dict)
        assert "phase" in result["mlsdm"]


class TestSDKGenerateTypedMethod:
    """Test the generate_typed() method contract."""

    def test_generate_typed_returns_dto(self):
        """Test generate_typed returns GenerateResponseDTO."""
        from mlsdm.sdk import GenerateResponseDTO, NeuroCognitiveClient

        client = NeuroCognitiveClient()
        result = client.generate_typed("Test prompt")

        assert isinstance(result, GenerateResponseDTO)

    def test_generate_typed_dto_has_required_fields(self):
        """Test GenerateResponseDTO has required fields."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        result = client.generate_typed("Test")

        # Core fields
        assert hasattr(result, "response")
        assert hasattr(result, "accepted")
        assert hasattr(result, "phase")

        # Type checks
        assert isinstance(result.response, str)
        assert isinstance(result.accepted, bool)
        assert isinstance(result.phase, str)

    def test_generate_typed_dto_phase_values(self):
        """Test GenerateResponseDTO phase is valid."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        result = client.generate_typed("Test")

        assert result.phase in ["wake", "sleep", "unknown"]

    def test_generate_typed_dto_has_cognitive_state(self):
        """Test GenerateResponseDTO has cognitive_state."""
        from mlsdm.sdk import CognitiveStateDTO, NeuroCognitiveClient

        client = NeuroCognitiveClient()
        result = client.generate_typed("Test")

        assert result.cognitive_state is not None
        assert isinstance(result.cognitive_state, CognitiveStateDTO)

    def test_generate_typed_cognitive_state_fields(self):
        """Test CognitiveStateDTO has expected fields."""
        from mlsdm.sdk import NeuroCognitiveClient

        client = NeuroCognitiveClient()
        result = client.generate_typed("Test")

        state = result.cognitive_state
        assert hasattr(state, "phase")
        assert hasattr(state, "stateless_mode")
        assert hasattr(state, "emergency_shutdown")

        assert isinstance(state.phase, str)
        assert isinstance(state.stateless_mode, bool)
        assert isinstance(state.emergency_shutdown, bool)


class TestSDKResponseDTOKeys:
    """Test that GenerateResponseDTO keys match contract."""

    def test_dto_keys_match_contract(self):
        """Test GENERATE_RESPONSE_DTO_KEYS matches expected contract."""
        from mlsdm.sdk import GENERATE_RESPONSE_DTO_KEYS

        expected_keys = {
            "response",
            "accepted",
            "phase",
            "moral_score",
            "aphasia_flags",
            "emergency_shutdown",
            "cognitive_state",
            "metrics",
            "safety_flags",
            "memory_stats",
            "governance",
            "timing",
            "validation_steps",
            "error",
            "rejected_at",
        }

        assert GENERATE_RESPONSE_DTO_KEYS == expected_keys


class TestSDKExceptions:
    """Test SDK exception hierarchy."""

    def test_mlsdm_error_is_base_exception(self):
        """Test MLSDMError is the base exception."""
        from mlsdm.sdk import MLSDMError

        assert issubclass(MLSDMError, Exception)

    def test_client_error_has_error_code(self):
        """Test MLSDMClientError can have error_code."""
        from mlsdm.sdk import MLSDMClientError

        error = MLSDMClientError("test", error_code="validation_error")
        assert error.error_code == "validation_error"

    def test_server_error_has_error_code(self):
        """Test MLSDMServerError can have error_code."""
        from mlsdm.sdk import MLSDMServerError

        error = MLSDMServerError("test", error_code="internal_error")
        assert error.error_code == "internal_error"

    def test_timeout_error_has_timeout_seconds(self):
        """Test MLSDMTimeoutError can have timeout_seconds."""
        from mlsdm.sdk import MLSDMTimeoutError

        error = MLSDMTimeoutError("test", timeout_seconds=30.0)
        assert error.timeout_seconds == 30.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
