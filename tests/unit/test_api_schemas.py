"""Tests for API schemas (CORE-09 API Contract).

Tests cover:
- GenerateRequest validation
- GenerateResponse structure
- CognitiveStateResponse fields
- HealthResponse/ReadinessResponse
- ErrorResponse format
"""

import pytest
from pydantic import ValidationError

from mlsdm.api.schemas import (
    CognitiveStateResponse,
    ErrorResponse,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    ReadinessResponse,
)


class TestGenerateRequest:
    """Tests for GenerateRequest schema."""

    def test_generate_request_valid_minimal(self):
        """Test GenerateRequest with minimal valid data."""
        req = GenerateRequest(prompt="Hello world")
        assert req.prompt == "Hello world"
        assert req.moral_value is None
        assert req.max_tokens is None

    def test_generate_request_with_all_fields(self):
        """Test GenerateRequest with all fields."""
        req = GenerateRequest(
            prompt="Test prompt",
            moral_value=0.75,
            max_tokens=100,
        )
        assert req.prompt == "Test prompt"
        assert req.moral_value == 0.75
        assert req.max_tokens == 100

    def test_generate_request_empty_prompt_fails(self):
        """Test that empty prompt fails validation."""
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="")

    def test_generate_request_moral_value_bounds(self):
        """Test moral_value bounds validation."""
        # Valid values
        req1 = GenerateRequest(prompt="test", moral_value=0.0)
        assert req1.moral_value == 0.0

        req2 = GenerateRequest(prompt="test", moral_value=1.0)
        assert req2.moral_value == 1.0

        # Invalid - below 0
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="test", moral_value=-0.1)

        # Invalid - above 1
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="test", moral_value=1.1)

    def test_generate_request_max_tokens_bounds(self):
        """Test max_tokens bounds validation."""
        # Valid values
        req1 = GenerateRequest(prompt="test", max_tokens=1)
        assert req1.max_tokens == 1

        req2 = GenerateRequest(prompt="test", max_tokens=4096)
        assert req2.max_tokens == 4096

        # Invalid - below 1
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="test", max_tokens=0)

        # Invalid - above 4096
        with pytest.raises(ValidationError):
            GenerateRequest(prompt="test", max_tokens=4097)


class TestCognitiveStateResponse:
    """Tests for CognitiveStateResponse schema."""

    def test_cognitive_state_minimal(self):
        """Test CognitiveStateResponse with minimal required fields."""
        state = CognitiveStateResponse(
            phase="wake",
            stateless_mode=False,
            emergency_shutdown=False,
        )
        assert state.phase == "wake"
        assert state.stateless_mode is False
        assert state.emergency_shutdown is False
        assert state.memory_used_mb is None
        assert state.moral_threshold is None

    def test_cognitive_state_with_all_fields(self):
        """Test CognitiveStateResponse with all fields."""
        state = CognitiveStateResponse(
            phase="sleep",
            stateless_mode=True,
            emergency_shutdown=True,
            memory_used_mb=123.45,
            moral_threshold=0.65,
        )
        assert state.phase == "sleep"
        assert state.stateless_mode is True
        assert state.emergency_shutdown is True
        assert state.memory_used_mb == 123.45
        assert state.moral_threshold == 0.65

    def test_cognitive_state_serialization(self):
        """Test that CognitiveStateResponse serializes correctly."""
        state = CognitiveStateResponse(
            phase="wake",
            stateless_mode=False,
            emergency_shutdown=False,
            memory_used_mb=50.0,
        )
        data = state.model_dump()
        assert data["phase"] == "wake"
        assert data["stateless_mode"] is False
        assert data["emergency_shutdown"] is False
        assert data["memory_used_mb"] == 50.0


class TestGenerateResponse:
    """Tests for GenerateResponse schema."""

    def test_generate_response_minimal(self):
        """Test GenerateResponse with minimal required fields."""
        resp = GenerateResponse(
            response="Generated text",
            accepted=True,
            phase="wake",
        )
        assert resp.response == "Generated text"
        assert resp.accepted is True
        assert resp.phase == "wake"
        assert resp.moral_score is None
        assert resp.emergency_shutdown is False

    def test_generate_response_with_all_fields(self):
        """Test GenerateResponse with all fields."""
        cognitive_state = CognitiveStateResponse(
            phase="wake",
            stateless_mode=False,
            emergency_shutdown=False,
        )

        resp = GenerateResponse(
            response="Test response",
            accepted=False,
            phase="sleep",
            moral_score=0.45,
            aphasia_flags={"is_aphasic": True, "severity": 0.3},
            emergency_shutdown=True,
            cognitive_state=cognitive_state,
            metrics={"total_ms": 123.45},
            safety_flags={"passed": True},
            memory_stats={"l1_size": 100},
        )
        assert resp.response == "Test response"
        assert resp.accepted is False
        assert resp.phase == "sleep"
        assert resp.moral_score == 0.45
        assert resp.aphasia_flags["is_aphasic"] is True
        assert resp.emergency_shutdown is True
        assert resp.cognitive_state is not None
        assert resp.metrics["total_ms"] == 123.45

    def test_generate_response_empty_string_allowed(self):
        """Test that empty response string is allowed (rejection case)."""
        resp = GenerateResponse(
            response="",
            accepted=False,
            phase="wake",
        )
        assert resp.response == ""
        assert resp.accepted is False

    def test_generate_response_serialization(self):
        """Test GenerateResponse serialization."""
        resp = GenerateResponse(
            response="Test",
            accepted=True,
            phase="wake",
            moral_score=0.8,
        )
        data = resp.model_dump()
        assert data["response"] == "Test"
        assert data["accepted"] is True
        assert data["phase"] == "wake"
        assert data["moral_score"] == 0.8


class TestHealthResponse:
    """Tests for HealthResponse schema."""

    def test_health_response_ok(self):
        """Test HealthResponse with ok status."""
        health = HealthResponse(status="ok")
        assert health.status == "ok"
        assert health.emergency_shutdown is False

    def test_health_response_degraded(self):
        """Test HealthResponse with degraded status."""
        health = HealthResponse(status="degraded")
        assert health.status == "degraded"

    def test_health_response_error(self):
        """Test HealthResponse with error status."""
        health = HealthResponse(status="error", emergency_shutdown=True)
        assert health.status == "error"
        assert health.emergency_shutdown is True

    def test_health_response_invalid_status(self):
        """Test that invalid status fails validation."""
        with pytest.raises(ValidationError):
            HealthResponse(status="invalid")  # type: ignore


class TestReadinessResponse:
    """Tests for ReadinessResponse schema."""

    def test_readiness_response_ready(self):
        """Test ReadinessResponse when ready."""
        ready = ReadinessResponse(ready=True, details={"all_systems": "go"})
        assert ready.ready is True
        assert ready.details["all_systems"] == "go"

    def test_readiness_response_not_ready(self):
        """Test ReadinessResponse when not ready."""
        ready = ReadinessResponse(
            ready=False,
            details={"database": "connecting", "llm": "unavailable"},
        )
        assert ready.ready is False
        assert ready.details["database"] == "connecting"

    def test_readiness_response_defaults_empty_details(self):
        """Test ReadinessResponse defaults to empty details dict."""
        ready = ReadinessResponse(ready=True)
        assert ready.ready is True
        assert ready.details == {}

    def test_readiness_response_serialization(self):
        """Test ReadinessResponse serialization."""
        ready = ReadinessResponse(ready=True, details={"check1": "pass"})
        data = ready.model_dump()
        assert data["ready"] is True
        assert data["details"]["check1"] == "pass"


class TestErrorResponse:
    """Tests for ErrorResponse schema."""

    def test_error_response_minimal(self):
        """Test ErrorResponse with minimal fields."""
        error = ErrorResponse(
            error_code="validation_error",
            message="Invalid input",
        )
        assert error.error_code == "validation_error"
        assert error.message == "Invalid input"
        assert error.debug_id is None

    def test_error_response_with_debug_id(self):
        """Test ErrorResponse with debug_id."""
        error = ErrorResponse(
            error_code="internal_error",
            message="Something went wrong",
            debug_id="abc123-def456",
        )
        assert error.error_code == "internal_error"
        assert error.message == "Something went wrong"
        assert error.debug_id == "abc123-def456"

    def test_error_response_serialization(self):
        """Test ErrorResponse serialization."""
        error = ErrorResponse(
            error_code="rate_limit_exceeded",
            message="Too many requests",
            debug_id="trace-xyz",
        )
        data = error.model_dump()
        assert data["error_code"] == "rate_limit_exceeded"
        assert data["message"] == "Too many requests"
        assert data["debug_id"] == "trace-xyz"


class TestSchemaIntegration:
    """Integration tests for schema compatibility."""

    def test_generate_response_with_cognitive_state_nesting(self):
        """Test GenerateResponse with nested CognitiveStateResponse."""
        cognitive = CognitiveStateResponse(
            phase="wake",
            stateless_mode=False,
            emergency_shutdown=False,
            memory_used_mb=75.5,
            moral_threshold=0.55,
        )

        resp = GenerateResponse(
            response="Nested test",
            accepted=True,
            phase="wake",
            cognitive_state=cognitive,
        )

        # Serialize and verify nesting
        data = resp.model_dump()
        assert data["cognitive_state"]["phase"] == "wake"
        assert data["cognitive_state"]["memory_used_mb"] == 75.5
        assert data["cognitive_state"]["moral_threshold"] == 0.55

    def test_schema_json_serialization(self):
        """Test that all schemas can serialize to JSON."""
        import json

        # Test each schema
        req = GenerateRequest(prompt="test")
        assert json.dumps(req.model_dump())

        state = CognitiveStateResponse(
            phase="wake",
            stateless_mode=False,
            emergency_shutdown=False,
        )
        assert json.dumps(state.model_dump())

        resp = GenerateResponse(response="test", accepted=True, phase="wake")
        assert json.dumps(resp.model_dump())

        health = HealthResponse(status="ok")
        assert json.dumps(health.model_dump())

        ready = ReadinessResponse(ready=True)
        assert json.dumps(ready.model_dump())

        error = ErrorResponse(error_code="test", message="test")
        assert json.dumps(error.model_dump())

    def test_schema_from_dict(self):
        """Test creating schemas from dictionaries."""
        # GenerateRequest from dict
        req_dict = {"prompt": "Hello", "moral_value": 0.7}
        req = GenerateRequest(**req_dict)
        assert req.prompt == "Hello"
        assert req.moral_value == 0.7

        # GenerateResponse from dict
        resp_dict = {"response": "Hi", "accepted": True, "phase": "wake"}
        resp = GenerateResponse(**resp_dict)
        assert resp.response == "Hi"
