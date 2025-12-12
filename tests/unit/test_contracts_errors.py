"""Tests for contracts/errors.py (ApiError model).

Tests cover:
- ApiError basic creation
- Factory methods (validation_error, rate_limit_exceeded, internal_error, moral_rejection)
- Serialization and model_dump
"""

import pytest
from pydantic import ValidationError

from mlsdm.contracts.errors import ApiError


class TestApiErrorBasic:
    """Tests for basic ApiError creation."""

    def test_api_error_minimal(self):
        """Test ApiError with minimal required fields."""
        error = ApiError(
            code="test_error",
            message="Test error message",
        )
        assert error.code == "test_error"
        assert error.message == "Test error message"
        assert error.details is None

    def test_api_error_with_details(self):
        """Test ApiError with details."""
        error = ApiError(
            code="validation_error",
            message="Invalid field",
            details={"field": "prompt", "constraint": "min_length=1"},
        )
        assert error.code == "validation_error"
        assert error.message == "Invalid field"
        assert error.details["field"] == "prompt"
        assert error.details["constraint"] == "min_length=1"

    def test_api_error_with_empty_strings(self):
        """Test that empty strings are allowed (no validation on min_length)."""
        # Empty code is allowed
        error1 = ApiError(code="", message="test")
        assert error1.code == ""
        
        # Empty message is allowed
        error2 = ApiError(code="test", message="")
        assert error2.message == ""

    def test_api_error_model_dump(self):
        """Test ApiError serialization."""
        error = ApiError(
            code="test_error",
            message="Test message",
            details={"key": "value"},
        )
        data = error.model_dump()
        assert data["code"] == "test_error"
        assert data["message"] == "Test message"
        assert data["details"]["key"] == "value"


class TestValidationErrorFactory:
    """Tests for validation_error factory method."""

    def test_validation_error_basic(self):
        """Test validation_error with message only."""
        error = ApiError.validation_error(message="Prompt cannot be empty")
        assert error.code == "validation_error"
        assert error.message == "Prompt cannot be empty"
        assert error.details is None

    def test_validation_error_with_field(self):
        """Test validation_error with field parameter."""
        error = ApiError.validation_error(
            message="Value must be positive",
            field="max_tokens",
        )
        assert error.code == "validation_error"
        assert error.message == "Value must be positive"
        assert error.details["field"] == "max_tokens"

    def test_validation_error_with_kwargs(self):
        """Test validation_error with additional kwargs."""
        error = ApiError.validation_error(
            message="Invalid value",
            field="moral_value",
            expected="0.0-1.0",
            actual=1.5,
        )
        assert error.code == "validation_error"
        assert error.details["field"] == "moral_value"
        assert error.details["expected"] == "0.0-1.0"
        assert error.details["actual"] == 1.5

    def test_validation_error_kwargs_without_field(self):
        """Test validation_error with kwargs but no field."""
        error = ApiError.validation_error(
            message="Multiple errors",
            count=3,
            severity="high",
        )
        assert error.code == "validation_error"
        assert error.details["count"] == 3
        assert error.details["severity"] == "high"


class TestRateLimitExceededFactory:
    """Tests for rate_limit_exceeded factory method."""

    def test_rate_limit_exceeded_default_message(self):
        """Test rate_limit_exceeded with default message."""
        error = ApiError.rate_limit_exceeded()
        assert error.code == "rate_limit_exceeded"
        assert "Rate limit exceeded" in error.message
        assert "try again later" in error.message

    def test_rate_limit_exceeded_custom_message(self):
        """Test rate_limit_exceeded with custom message."""
        error = ApiError.rate_limit_exceeded(
            message="Too many requests. Retry after 60 seconds."
        )
        assert error.code == "rate_limit_exceeded"
        assert error.message == "Too many requests. Retry after 60 seconds."


class TestInternalErrorFactory:
    """Tests for internal_error factory method."""

    def test_internal_error_default_message(self):
        """Test internal_error with default message."""
        error = ApiError.internal_error()
        assert error.code == "internal_error"
        assert "internal error occurred" in error.message
        assert "try again later" in error.message

    def test_internal_error_custom_message(self):
        """Test internal_error with custom message."""
        error = ApiError.internal_error(
            message="Database connection failed. Contact support."
        )
        assert error.code == "internal_error"
        assert error.message == "Database connection failed. Contact support."


class TestMoralRejectionFactory:
    """Tests for moral_rejection factory method."""

    def test_moral_rejection_default_stage(self):
        """Test moral_rejection with default stage."""
        error = ApiError.moral_rejection(score=0.3, threshold=0.5)
        assert error.code == "moral_rejection"
        assert "0.30" in error.message
        assert "0.50" in error.message
        assert "pre_flight" in error.message
        assert error.details["score"] == 0.3
        assert error.details["threshold"] == 0.5
        assert error.details["stage"] == "pre_flight"

    def test_moral_rejection_custom_stage(self):
        """Test moral_rejection with custom stage."""
        error = ApiError.moral_rejection(
            score=0.25,
            threshold=0.6,
            stage="post_generation",
        )
        assert error.code == "moral_rejection"
        assert "0.25" in error.message
        assert "0.60" in error.message
        assert "post_generation" in error.message
        assert error.details["stage"] == "post_generation"

    def test_moral_rejection_details_structure(self):
        """Test moral_rejection details structure."""
        error = ApiError.moral_rejection(score=0.45, threshold=0.55, stage="runtime")
        assert error.details is not None
        assert "score" in error.details
        assert "threshold" in error.details
        assert "stage" in error.details
        assert error.details["score"] == 0.45
        assert error.details["threshold"] == 0.55
        assert error.details["stage"] == "runtime"


class TestApiErrorSerialization:
    """Tests for ApiError serialization and JSON compatibility."""

    def test_api_error_json_serialization(self):
        """Test that ApiError can be serialized to JSON."""
        import json

        error = ApiError(
            code="test_error",
            message="Test message",
            details={"key": "value"},
        )
        json_str = json.dumps(error.model_dump())
        parsed = json.loads(json_str)
        assert parsed["code"] == "test_error"
        assert parsed["message"] == "Test message"
        assert parsed["details"]["key"] == "value"

    def test_factory_methods_serialize(self):
        """Test that all factory methods produce serializable errors."""
        import json

        errors = [
            ApiError.validation_error("test", field="test_field"),
            ApiError.rate_limit_exceeded(),
            ApiError.internal_error(),
            ApiError.moral_rejection(score=0.4, threshold=0.6),
        ]

        for error in errors:
            # Should be serializable
            json_str = json.dumps(error.model_dump())
            parsed = json.loads(json_str)
            assert "code" in parsed
            assert "message" in parsed

    def test_api_error_from_dict(self):
        """Test creating ApiError from dictionary."""
        data = {
            "code": "test_error",
            "message": "Test message",
            "details": {"field": "test"},
        }
        error = ApiError(**data)
        assert error.code == "test_error"
        assert error.message == "Test message"
        assert error.details["field"] == "test"


class TestApiErrorEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_api_error_with_empty_details_dict(self):
        """Test ApiError with empty details dict."""
        error = ApiError(
            code="test",
            message="test",
            details={},
        )
        assert error.details == {}

    def test_api_error_with_nested_details(self):
        """Test ApiError with nested details structure."""
        error = ApiError(
            code="complex_error",
            message="Complex error",
            details={
                "field": "prompt",
                "validation": {
                    "min_length": 1,
                    "max_length": 1000,
                    "actual": 0,
                },
            },
        )
        assert error.details["field"] == "prompt"
        assert error.details["validation"]["min_length"] == 1
        assert error.details["validation"]["actual"] == 0

    def test_moral_rejection_with_zero_values(self):
        """Test moral_rejection with zero score and threshold."""
        error = ApiError.moral_rejection(score=0.0, threshold=0.0)
        assert error.details["score"] == 0.0
        assert error.details["threshold"] == 0.0
        assert "0.00" in error.message

    def test_moral_rejection_with_max_values(self):
        """Test moral_rejection with maximum values."""
        error = ApiError.moral_rejection(score=1.0, threshold=1.0)
        assert error.details["score"] == 1.0
        assert error.details["threshold"] == 1.0
        assert "1.00" in error.message

    def test_validation_error_with_none_field(self):
        """Test validation_error explicitly passing None as field."""
        error = ApiError.validation_error(message="Generic error", field=None)
        assert error.code == "validation_error"
        assert error.message == "Generic error"
        # Field should not be in details if None
        assert error.details is None or "field" not in (error.details or {})


class TestApiErrorExamples:
    """Tests using examples from docstring."""

    def test_docstring_example(self):
        """Test the example from ApiError docstring."""
        error = ApiError(
            code="validation_error",
            message="Prompt cannot be empty",
            details={"field": "prompt", "constraint": "min_length=1"},
        )
        result = error.model_dump()
        assert result["code"] == "validation_error"
        assert result["message"] == "Prompt cannot be empty"
        assert result["details"]["field"] == "prompt"
        assert result["details"]["constraint"] == "min_length=1"
