"""
EngineResult contract validation tests.

These tests ensure the EngineResult contract model maintains its structure
and can correctly serialize/deserialize across versions.

The EngineResult is the primary output contract for the NeuroCognitiveEngine.generate()
method and must remain stable.
"""

import pytest

from mlsdm.contracts.engine_models import (
    EngineErrorInfo,
    EngineResult,
    EngineTiming,
    EngineValidationStep,
)


class TestEngineResultContract:
    """Test EngineResult contract stability and serialization."""
    
    def test_engine_result_success_case(self):
        """Test EngineResult for successful generation."""
        # Create a successful result
        timing = EngineTiming(
            total=100.0,
            moral_precheck=10.0,
            generation=80.0,
            post_moral_check=10.0,
        )
        
        validation_steps = [
            EngineValidationStep(
                step="moral_precheck",
                passed=True,
                score=0.8,
                threshold=0.5,
            ),
            EngineValidationStep(
                step="post_moral_check",
                passed=True,
                score=0.8,
                threshold=0.5,
            ),
        ]
        
        result = EngineResult(
            response="Hello, world!",
            timing=timing,
            validation_steps=validation_steps,
            error=None,
        )
        
        # Validate structure
        assert result.response == "Hello, world!"
        assert result.timing.total == 100.0
        assert len(result.validation_steps) == 2
        assert result.error is None
        
        # Test serialization
        dict_form = result.model_dump()
        assert dict_form["response"] == "Hello, world!"
        assert dict_form["timing"]["total"] == 100.0
        assert dict_form["error"] is None
        
        # Test deserialization
        reconstructed = EngineResult(**dict_form)
        assert reconstructed.response == result.response
        assert reconstructed.timing.total == result.timing.total
    
    def test_engine_result_error_case(self):
        """Test EngineResult for failed generation."""
        timing = EngineTiming(total=50.0, moral_precheck=50.0)
        
        validation_steps = [
            EngineValidationStep(
                step="moral_precheck",
                passed=False,
                score=0.2,
                threshold=0.5,
                reason="Below moral threshold",
            ),
        ]
        
        error = EngineErrorInfo(
            type="moral_precheck",
            message="Input rejected by moral filter",
            score=0.2,
            threshold=0.5,
        )
        
        result = EngineResult(
            response="",
            timing=timing,
            validation_steps=validation_steps,
            error=error,
        )
        
        # Validate structure
        assert result.response == ""
        assert result.error is not None
        assert result.error.type == "moral_precheck"
        assert result.validation_steps[0].passed is False
        
        # Test serialization
        dict_form = result.model_dump()
        assert dict_form["error"]["type"] == "moral_precheck"
        
        # Test deserialization
        reconstructed = EngineResult(**dict_form)
        assert reconstructed.error.type == error.type
    
    def test_engine_result_from_dict(self):
        """Test EngineResult.from_dict() compatibility method."""
        # Legacy dict format (pre-Pydantic)
        legacy_dict = {
            "response": "Test response",
            "timing": {
                "total": 100.0,
                "moral_precheck": 20.0,
                "generation": 70.0,
                "post_moral_check": 10.0,
            },
            "validation_steps": [
                {
                    "step": "moral_precheck",
                    "passed": True,
                    "score": 0.8,
                    "threshold": 0.5,
                }
            ],
            "error": None,
        }
        
        # Should be able to construct from dict
        result = EngineResult.from_dict(legacy_dict)
        
        assert result.response == "Test response"
        assert result.timing.total == 100.0
        assert len(result.validation_steps) == 1
        assert result.error is None
    
    def test_engine_result_with_partial_timing(self):
        """Test EngineResult handles partial timing data."""
        # Minimal timing (only total)
        timing = EngineTiming(total=50.0)
        
        result = EngineResult(
            response="Response",
            timing=timing,
            validation_steps=[],
            error=None,
        )
        
        assert result.timing.total == 50.0
        assert result.timing.moral_precheck is None
        assert result.timing.generation is None
        
        # Serialization should preserve None values
        dict_form = result.model_dump()
        assert dict_form["timing"]["total"] == 50.0
        assert dict_form["timing"]["moral_precheck"] is None


class TestEngineTiming Contract:
    """Test EngineTiming contract stability."""
    
    def test_timing_required_field(self):
        """Test total is the only required field."""
        # Should work with just total
        timing = EngineTiming(total=100.0)
        assert timing.total == 100.0
        
        # All optional fields should be None
        assert timing.moral_precheck is None
        assert timing.grammar_precheck is None
        assert timing.generation is None
        assert timing.post_moral_check is None
    
    def test_timing_all_fields(self):
        """Test timing with all fields populated."""
        timing = EngineTiming(
            total=100.0,
            moral_precheck=10.0,
            grammar_precheck=5.0,
            generation=75.0,
            post_moral_check=10.0,
        )
        
        assert timing.total == 100.0
        assert timing.moral_precheck == 10.0
        assert timing.grammar_precheck == 5.0
        assert timing.generation == 75.0
        assert timing.post_moral_check == 10.0
    
    def test_timing_validation(self):
        """Test timing field validation (non-negative)."""
        # Positive values should work
        timing = EngineTiming(total=100.0, moral_precheck=10.0)
        assert timing.total == 100.0
        
        # Zero should work
        timing_zero = EngineTiming(total=0.0)
        assert timing_zero.total == 0.0
        
        # Negative values should fail validation
        with pytest.raises(Exception):  # Pydantic ValidationError
            EngineTiming(total=-1.0)
    
    def test_timing_from_dict(self):
        """Test EngineTiming.from_dict() compatibility."""
        timing_dict = {
            "total": 100.0,
            "moral_precheck": 20.0,
            "generation": 70.0,
        }
        
        timing = EngineTiming.from_dict(timing_dict)
        
        assert timing.total == 100.0
        assert timing.moral_precheck == 20.0
        assert timing.generation == 70.0
        assert timing.grammar_precheck is None  # Not in dict


class TestEngineValidationStepContract:
    """Test EngineValidationStep contract stability."""
    
    def test_validation_step_required_fields(self):
        """Test step and passed are required."""
        # Should work with just step and passed
        step = EngineValidationStep(step="moral_precheck", passed=True)
        
        assert step.step == "moral_precheck"
        assert step.passed is True
        assert step.skipped is False  # Default
        assert step.score is None
        assert step.threshold is None
        assert step.reason is None
    
    def test_validation_step_full_fields(self):
        """Test validation step with all fields."""
        step = EngineValidationStep(
            step="moral_precheck",
            passed=True,
            skipped=False,
            score=0.8,
            threshold=0.5,
            reason=None,
        )
        
        assert step.step == "moral_precheck"
        assert step.passed is True
        assert step.score == 0.8
        assert step.threshold == 0.5
    
    def test_validation_step_skipped(self):
        """Test validation step marked as skipped."""
        step = EngineValidationStep(
            step="grammar_precheck",
            passed=False,
            skipped=True,
            reason="Grammar checking disabled",
        )
        
        assert step.skipped is True
        assert step.reason == "Grammar checking disabled"


class TestEngineErrorInfoContract:
    """Test EngineErrorInfo contract stability."""
    
    def test_error_info_required_fields(self):
        """Test type is the only required field."""
        error = EngineErrorInfo(type="moral_precheck")
        
        assert error.type == "moral_precheck"
        assert error.message is None
        assert error.score is None
        assert error.threshold is None
        assert error.traceback is None
    
    def test_error_info_moral_rejection(self):
        """Test error info for moral rejection."""
        error = EngineErrorInfo(
            type="moral_precheck",
            message="Input rejected by moral filter",
            score=0.2,
            threshold=0.5,
        )
        
        assert error.type == "moral_precheck"
        assert error.message == "Input rejected by moral filter"
        assert error.score == 0.2
        assert error.threshold == 0.5
    
    def test_error_info_from_dict(self):
        """Test EngineErrorInfo.from_dict() compatibility."""
        error_dict = {
            "type": "internal_error",
            "message": "Something went wrong",
            "traceback": "Traceback...",
        }
        
        error = EngineErrorInfo.from_dict(error_dict)
        
        assert error.type == "internal_error"
        assert error.message == "Something went wrong"
        assert error.traceback == "Traceback..."


# Mark all tests as contract tests
pytestmark = pytest.mark.security
