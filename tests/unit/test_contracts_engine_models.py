"""Tests for contracts/engine_models.py (Engine contract models).

Tests cover:
- EngineTiming
- EngineValidationStep
- EngineErrorInfo
- EngineResultMeta
- EngineResult
- Factory methods and properties
"""

import pytest
from pydantic import ValidationError

from mlsdm.contracts.engine_models import (
    EngineErrorInfo,
    EngineResult,
    EngineResultMeta,
    EngineTiming,
    EngineValidationStep,
)


class TestEngineTiming:
    """Tests for EngineTiming model."""

    def test_engine_timing_defaults(self):
        """Test EngineTiming with default values."""
        timing = EngineTiming()
        assert timing.total == 0.0
        assert timing.moral_precheck is None
        assert timing.grammar_precheck is None
        assert timing.generation is None
        assert timing.post_moral_check is None

    def test_engine_timing_with_all_fields(self):
        """Test EngineTiming with all fields populated."""
        timing = EngineTiming(
            total=123.45,
            moral_precheck=10.5,
            grammar_precheck=8.2,
            generation=95.0,
            post_moral_check=9.75,
        )
        assert timing.total == 123.45
        assert timing.moral_precheck == 10.5
        assert timing.grammar_precheck == 8.2
        assert timing.generation == 95.0
        assert timing.post_moral_check == 9.75

    def test_engine_timing_negative_values_fail(self):
        """Test that negative timing values fail validation."""
        with pytest.raises(ValidationError):
            EngineTiming(total=-1.0)

        with pytest.raises(ValidationError):
            EngineTiming(moral_precheck=-5.0)

    def test_engine_timing_from_dict_full(self):
        """Test EngineTiming.from_dict with full data."""
        timing_dict = {
            "total": 100.0,
            "moral_precheck": 10.0,
            "grammar_precheck": 5.0,
            "generation": 80.0,
            "post_moral_check": 5.0,
        }
        timing = EngineTiming.from_dict(timing_dict)
        assert timing.total == 100.0
        assert timing.moral_precheck == 10.0
        assert timing.generation == 80.0

    def test_engine_timing_from_dict_partial(self):
        """Test EngineTiming.from_dict with partial data."""
        timing_dict = {
            "total": 50.0,
            "generation": 45.0,
        }
        timing = EngineTiming.from_dict(timing_dict)
        assert timing.total == 50.0
        assert timing.generation == 45.0
        assert timing.moral_precheck is None

    def test_engine_timing_from_dict_empty(self):
        """Test EngineTiming.from_dict with empty dict."""
        timing = EngineTiming.from_dict({})
        assert timing.total == 0.0
        assert timing.moral_precheck is None

    def test_engine_timing_serialization(self):
        """Test EngineTiming serialization."""
        timing = EngineTiming(total=100.0, generation=90.0)
        data = timing.model_dump()
        assert data["total"] == 100.0
        assert data["generation"] == 90.0


class TestEngineValidationStep:
    """Tests for EngineValidationStep model."""

    def test_validation_step_minimal(self):
        """Test EngineValidationStep with minimal fields."""
        step = EngineValidationStep(
            step="moral_precheck",
            passed=True,
        )
        assert step.step == "moral_precheck"
        assert step.passed is True
        assert step.skipped is False
        assert step.score is None
        assert step.threshold is None
        assert step.reason is None

    def test_validation_step_with_all_fields(self):
        """Test EngineValidationStep with all fields."""
        step = EngineValidationStep(
            step="post_moral_check",
            passed=False,
            skipped=False,
            score=0.35,
            threshold=0.50,
            reason="Score below threshold",
        )
        assert step.step == "post_moral_check"
        assert step.passed is False
        assert step.score == 0.35
        assert step.threshold == 0.50
        assert step.reason == "Score below threshold"

    def test_validation_step_skipped(self):
        """Test EngineValidationStep for skipped step."""
        step = EngineValidationStep(
            step="grammar_precheck",
            passed=False,
            skipped=True,
            reason="FSLGS disabled",
        )
        assert step.step == "grammar_precheck"
        assert step.passed is False
        assert step.skipped is True
        assert step.reason == "FSLGS disabled"


class TestEngineErrorInfo:
    """Tests for EngineErrorInfo model."""

    def test_engine_error_info_minimal(self):
        """Test EngineErrorInfo with minimal fields."""
        error = EngineErrorInfo(type="internal_error")
        assert error.type == "internal_error"
        assert error.message is None
        assert error.score is None
        assert error.threshold is None
        assert error.traceback is None

    def test_engine_error_info_moral_rejection(self):
        """Test EngineErrorInfo for moral rejection."""
        error = EngineErrorInfo(
            type="moral_precheck",
            message="Moral score below threshold",
            score=0.3,
            threshold=0.5,
        )
        assert error.type == "moral_precheck"
        assert error.message == "Moral score below threshold"
        assert error.score == 0.3
        assert error.threshold == 0.5

    def test_engine_error_info_with_traceback(self):
        """Test EngineErrorInfo with traceback."""
        error = EngineErrorInfo(
            type="internal_error",
            message="Exception occurred",
            traceback="Traceback (most recent call last)...",
        )
        assert error.type == "internal_error"
        assert error.traceback is not None

    def test_engine_error_info_from_dict_full(self):
        """Test EngineErrorInfo.from_dict with full data."""
        error_dict = {
            "type": "mlsdm_rejection",
            "message": "Request rejected",
            "score": 0.4,
            "threshold": 0.6,
            "traceback": "stack trace",
        }
        error = EngineErrorInfo.from_dict(error_dict)
        assert error.type == "mlsdm_rejection"
        assert error.message == "Request rejected"
        assert error.score == 0.4
        assert error.threshold == 0.6

    def test_engine_error_info_from_dict_minimal(self):
        """Test EngineErrorInfo.from_dict with minimal data."""
        error = EngineErrorInfo.from_dict({})
        assert error.type == "unknown"
        assert error.message is None


class TestEngineResultMeta:
    """Tests for EngineResultMeta model."""

    def test_engine_result_meta_defaults(self):
        """Test EngineResultMeta with default values."""
        meta = EngineResultMeta()
        assert meta.backend_id is None
        assert meta.variant is None

    def test_engine_result_meta_with_backend_id(self):
        """Test EngineResultMeta with backend_id."""
        meta = EngineResultMeta(backend_id="openai-gpt4")
        assert meta.backend_id == "openai-gpt4"
        assert meta.variant is None

    def test_engine_result_meta_with_variant(self):
        """Test EngineResultMeta with A/B test variant."""
        meta = EngineResultMeta(backend_id="openai", variant="variant_b")
        assert meta.backend_id == "openai"
        assert meta.variant == "variant_b"

    def test_engine_result_meta_from_dict(self):
        """Test EngineResultMeta.from_dict."""
        meta_dict = {"backend_id": "anthropic", "variant": "control"}
        meta = EngineResultMeta.from_dict(meta_dict)
        assert meta.backend_id == "anthropic"
        assert meta.variant == "control"

    def test_engine_result_meta_from_dict_empty(self):
        """Test EngineResultMeta.from_dict with empty dict."""
        meta = EngineResultMeta.from_dict({})
        assert meta.backend_id is None
        assert meta.variant is None


class TestEngineResult:
    """Tests for EngineResult model."""

    def test_engine_result_minimal(self):
        """Test EngineResult with minimal fields."""
        result = EngineResult()
        assert result.response == ""
        assert result.governance is None
        assert result.mlsdm == {}
        assert isinstance(result.timing, EngineTiming)
        assert result.validation_steps == []
        assert result.error is None
        assert result.rejected_at is None
        assert isinstance(result.meta, EngineResultMeta)

    def test_engine_result_successful_generation(self):
        """Test EngineResult for successful generation."""
        result = EngineResult(
            response="Generated response text",
            timing=EngineTiming(total=100.0, generation=95.0),
        )
        assert result.response == "Generated response text"
        assert result.error is None
        assert result.is_success is True
        assert result.is_rejected is False

    def test_engine_result_rejected_generation(self):
        """Test EngineResult for rejected generation."""
        result = EngineResult(
            response="",
            error=EngineErrorInfo(type="moral_precheck", message="Rejected"),
            rejected_at="pre_flight",
        )
        assert result.response == ""
        assert result.error is not None
        assert result.rejected_at == "pre_flight"
        assert result.is_success is False
        assert result.is_rejected is True

    def test_engine_result_is_success_property(self):
        """Test is_success property."""
        # Success case: no error, no rejection, has response
        result1 = EngineResult(response="text")
        assert result1.is_success is True

        # Failure with error
        result2 = EngineResult(
            response="",
            error=EngineErrorInfo(type="error"),
        )
        assert result2.is_success is False

        # Failure with rejection
        result3 = EngineResult(response="", rejected_at="pre_flight")
        assert result3.is_success is False

        # Failure with empty response (no error/rejection but no output)
        result4 = EngineResult(response="")
        assert result4.is_success is False

        # Success requires all three conditions
        result5 = EngineResult(response="valid output", error=None, rejected_at=None)
        assert result5.is_success is True

    def test_engine_result_is_rejected_property(self):
        """Test is_rejected property."""
        result1 = EngineResult(rejected_at="generation")
        assert result1.is_rejected is True

        result2 = EngineResult()
        assert result2.is_rejected is False

    def test_engine_result_with_validation_steps(self):
        """Test EngineResult with validation steps."""
        steps = [
            EngineValidationStep(step="moral_precheck", passed=True),
            EngineValidationStep(step="grammar_precheck", passed=True, skipped=True),
        ]
        result = EngineResult(
            response="text",
            validation_steps=steps,
        )
        assert len(result.validation_steps) == 2
        assert result.validation_steps[0].step == "moral_precheck"
        assert result.validation_steps[1].skipped is True

    def test_engine_result_from_dict_full(self):
        """Test EngineResult.from_dict with full data."""
        result_dict = {
            "response": "Generated text",
            "governance": {"mode": "action"},
            "mlsdm": {"phase": "wake"},
            "timing": {"total": 100.0, "generation": 90.0},
            "validation_steps": [
                {"step": "moral_precheck", "passed": True, "score": 0.8},
            ],
            "error": None,
            "rejected_at": None,
            "meta": {"backend_id": "openai", "variant": "control"},
        }
        result = EngineResult.from_dict(result_dict)
        assert result.response == "Generated text"
        assert result.governance["mode"] == "action"
        assert result.mlsdm["phase"] == "wake"
        assert result.timing.total == 100.0
        assert len(result.validation_steps) == 1
        assert result.meta.backend_id == "openai"

    def test_engine_result_from_dict_minimal(self):
        """Test EngineResult.from_dict with minimal data."""
        result = EngineResult.from_dict({})
        assert result.response == ""
        assert result.mlsdm == {}
        assert result.timing.total == 0.0

    def test_engine_result_from_dict_with_error(self):
        """Test EngineResult.from_dict with error."""
        result_dict = {
            "response": "",
            "error": {
                "type": "moral_precheck",
                "message": "Rejected",
                "score": 0.3,
                "threshold": 0.5,
            },
            "rejected_at": "pre_flight",
        }
        result = EngineResult.from_dict(result_dict)
        assert result.error is not None
        assert result.error.type == "moral_precheck"
        assert result.error.score == 0.3
        assert result.rejected_at == "pre_flight"

    def test_engine_result_to_dict(self):
        """Test EngineResult.to_dict conversion."""
        result = EngineResult(
            response="Test",
            timing=EngineTiming(total=50.0),
        )
        data = result.to_dict()
        assert data["response"] == "Test"
        assert data["timing"]["total"] == 50.0
        assert "validation_steps" in data

    def test_engine_result_round_trip(self):
        """Test EngineResult from_dict -> to_dict round trip."""
        original = {
            "response": "Round trip test",
            "timing": {"total": 100.0, "generation": 95.0},
            "validation_steps": [
                {"step": "test_step", "passed": True},
            ],
        }
        result = EngineResult.from_dict(original)
        converted = result.to_dict()
        assert converted["response"] == original["response"]
        assert converted["timing"]["total"] == original["timing"]["total"]


class TestEngineResultLiteralRejectedAt:
    """Tests for rejected_at literal validation."""

    def test_engine_result_valid_rejected_at_values(self):
        """Test valid rejected_at literal values."""
        result1 = EngineResult(rejected_at="pre_flight")
        assert result1.rejected_at == "pre_flight"

        result2 = EngineResult(rejected_at="generation")
        assert result2.rejected_at == "generation"

        result3 = EngineResult(rejected_at="pre_moral")
        assert result3.rejected_at == "pre_moral"

    def test_engine_result_invalid_rejected_at_value(self):
        """Test invalid rejected_at value fails validation."""
        with pytest.raises(ValidationError):
            EngineResult(rejected_at="invalid_stage")  # type: ignore


class TestEngineModelSerialization:
    """Tests for serialization of all engine models."""

    def test_all_models_serialize_to_json(self):
        """Test that all models can serialize to JSON."""
        import json

        # EngineTiming
        timing = EngineTiming(total=100.0)
        assert json.dumps(timing.model_dump())

        # EngineValidationStep
        step = EngineValidationStep(step="test", passed=True)
        assert json.dumps(step.model_dump())

        # EngineErrorInfo
        error = EngineErrorInfo(type="test_error")
        assert json.dumps(error.model_dump())

        # EngineResultMeta
        meta = EngineResultMeta(backend_id="test")
        assert json.dumps(meta.model_dump())

        # EngineResult
        result = EngineResult(response="test")
        assert json.dumps(result.to_dict())
