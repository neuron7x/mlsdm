"""Tests for contracts/speech_models.py (Speech governance contract models).

Tests cover:
- AphasiaReport
- PipelineStepResult
- PipelineMetadata
- AphasiaMetadata
"""

import pytest
from pydantic import ValidationError

from mlsdm.contracts.speech_models import (
    AphasiaMetadata,
    AphasiaReport,
    PipelineMetadata,
    PipelineStepResult,
)


class TestAphasiaReport:
    """Tests for AphasiaReport model."""

    def test_aphasia_report_defaults(self):
        """Test AphasiaReport with default values."""
        report = AphasiaReport()
        assert report.is_aphasic is False
        assert report.severity == 0.0
        assert report.patterns_detected == []
        assert report.repaired is False
        assert report.repair_notes is None

    def test_aphasia_report_detected(self):
        """Test AphasiaReport when aphasia is detected."""
        report = AphasiaReport(
            is_aphasic=True,
            severity=0.6,
            patterns_detected=["missing_articles", "omitted_function_words"],
        )
        assert report.is_aphasic is True
        assert report.severity == 0.6
        assert len(report.patterns_detected) == 2
        assert "missing_articles" in report.patterns_detected

    def test_aphasia_report_with_repair(self):
        """Test AphasiaReport with repair applied."""
        report = AphasiaReport(
            is_aphasic=True,
            severity=0.5,
            patterns_detected=["missing_articles"],
            repaired=True,
            repair_notes="Added missing articles and function words",
        )
        assert report.repaired is True
        assert report.repair_notes is not None
        assert "articles" in report.repair_notes

    def test_aphasia_report_severity_bounds(self):
        """Test AphasiaReport severity validation."""
        # Valid bounds
        report1 = AphasiaReport(severity=0.0)
        assert report1.severity == 0.0

        report2 = AphasiaReport(severity=1.0)
        assert report2.severity == 1.0

        # Invalid - below 0
        with pytest.raises(ValidationError):
            AphasiaReport(severity=-0.1)

        # Invalid - above 1
        with pytest.raises(ValidationError):
            AphasiaReport(severity=1.1)

    def test_aphasia_report_none_detected_factory(self):
        """Test none_detected factory method."""
        report = AphasiaReport.none_detected()
        assert report.is_aphasic is False
        assert report.severity == 0.0
        assert report.patterns_detected == []
        assert report.repaired is False

    def test_aphasia_report_serialization(self):
        """Test AphasiaReport serialization."""
        report = AphasiaReport(
            is_aphasic=True,
            severity=0.7,
            patterns_detected=["pattern1", "pattern2"],
        )
        data = report.model_dump()
        assert data["is_aphasic"] is True
        assert data["severity"] == 0.7
        assert len(data["patterns_detected"]) == 2


class TestPipelineStepResult:
    """Tests for PipelineStepResult model."""

    def test_pipeline_step_result_minimal(self):
        """Test PipelineStepResult with minimal fields."""
        step = PipelineStepResult(
            name="test_governor",
            status="ok",
        )
        assert step.name == "test_governor"
        assert step.status == "ok"
        assert step.raw_text is None
        assert step.final_text is None
        assert step.error_message is None

    def test_pipeline_step_result_with_text(self):
        """Test PipelineStepResult with text fields."""
        step = PipelineStepResult(
            name="test_governor",
            status="ok",
            raw_text="input text",
            final_text="output text",
        )
        assert step.raw_text == "input text"
        assert step.final_text == "output text"

    def test_pipeline_step_result_with_error(self):
        """Test PipelineStepResult with error status."""
        step = PipelineStepResult(
            name="failing_governor",
            status="error",
            error_type="TimeoutError",
            error_message="Governor failed: connection timeout",
        )
        assert step.status == "error"
        assert step.error_type == "TimeoutError"
        assert step.error_message is not None
        assert "timeout" in step.error_message

    def test_pipeline_step_result_is_success_property(self):
        """Test is_success property."""
        step_ok = PipelineStepResult(name="test", status="ok")
        assert step_ok.is_success is True

        step_error = PipelineStepResult(name="test", status="error")
        assert step_error.is_success is False

    def test_pipeline_step_result_is_error_property(self):
        """Test is_error property."""
        step_ok = PipelineStepResult(name="test", status="ok")
        assert step_ok.is_error is False

        step_error = PipelineStepResult(name="test", status="error")
        assert step_error.is_error is True

    def test_pipeline_step_result_with_metadata(self):
        """Test PipelineStepResult with metadata."""
        step = PipelineStepResult(
            name="test_governor",
            status="ok",
            metadata={"patterns_fixed": 3, "confidence": 0.95},
        )
        assert step.metadata is not None
        assert step.metadata["patterns_fixed"] == 3

    def test_pipeline_step_result_serialization(self):
        """Test PipelineStepResult serialization."""
        step = PipelineStepResult(
            name="test_step",
            status="ok",
            raw_text="in",
            final_text="out",
        )
        data = step.model_dump()
        assert data["name"] == "test_step"
        assert data["status"] == "ok"
        assert data["raw_text"] == "in"
        assert data["final_text"] == "out"


class TestPipelineMetadata:
    """Tests for PipelineMetadata model."""

    def test_pipeline_metadata_defaults(self):
        """Test PipelineMetadata with default values."""
        meta = PipelineMetadata()
        assert meta.pipeline == []
        assert meta.aphasia_report is None
        assert meta.total_steps == 0
        assert meta.successful_steps == 0
        assert meta.failed_steps == 0

    def test_pipeline_metadata_with_steps(self):
        """Test PipelineMetadata with pipeline steps."""
        step1 = PipelineStepResult(name="step1", status="ok")
        step2 = PipelineStepResult(name="step2", status="error")
        
        meta = PipelineMetadata(
            pipeline=[step1, step2],
            total_steps=2,
            successful_steps=1,
            failed_steps=1,
        )
        assert len(meta.pipeline) == 2
        assert meta.total_steps == 2
        assert meta.successful_steps == 1
        assert meta.failed_steps == 1

    def test_pipeline_metadata_with_aphasia_report(self):
        """Test PipelineMetadata with aphasia report."""
        aphasia = AphasiaReport(is_aphasic=True, severity=0.5)
        meta = PipelineMetadata(aphasia_report=aphasia)
        
        assert meta.aphasia_report is not None
        assert meta.aphasia_report.is_aphasic is True

    def test_pipeline_metadata_from_history(self):
        """Test PipelineMetadata.from_history factory method."""
        history = [
            {"name": "step1", "status": "ok", "raw_text": "in", "final_text": "out"},
            {"name": "step2", "status": "error", "error_type": "TestError"},
        ]
        meta = PipelineMetadata.from_history(history)
        
        assert len(meta.pipeline) == 2
        assert meta.successful_steps == 1
        assert meta.failed_steps == 1
        assert meta.pipeline[0].status == "ok"
        assert meta.pipeline[1].status == "error"

    def test_pipeline_metadata_from_history_with_aphasia(self):
        """Test from_history with aphasia report."""
        history = [{"name": "step1", "status": "ok"}]
        aphasia = AphasiaReport(is_aphasic=True, severity=0.4)
        meta = PipelineMetadata.from_history(history, aphasia_report=aphasia)
        
        assert meta.aphasia_report is not None
        assert meta.aphasia_report.severity == 0.4

    def test_pipeline_metadata_from_history_missing_status(self):
        """Test from_history handles missing status field."""
        history = [{"name": "bad_step"}]  # No status field
        meta = PipelineMetadata.from_history(history)
        
        assert len(meta.pipeline) == 1
        assert meta.pipeline[0].status == "error"
        assert "missing status" in meta.pipeline[0].error_message


class TestAphasiaMetadata:
    """Tests for AphasiaMetadata model."""

    def test_aphasia_metadata_exists(self):
        """Test that AphasiaMetadata can be imported."""
        # Just verify it exists and can be imported
        assert AphasiaMetadata is not None
        # Test basic instantiation with required fields
        # (actual fields depend on implementation)


class TestSpeechModelSerialization:
    """Tests for serialization of all speech models."""

    def test_all_models_serialize_to_json(self):
        """Test that all speech models can serialize to JSON."""
        import json

        # AphasiaReport
        aphasia = AphasiaReport(is_aphasic=True, severity=0.5)
        assert json.dumps(aphasia.model_dump())

        # PipelineStepResult
        step = PipelineStepResult(
            name="test",
            status="ok",
            raw_text="in",
            final_text="out",
        )
        assert json.dumps(step.model_dump())

        # PipelineMetadata
        meta = PipelineMetadata(pipeline=[step])
        assert json.dumps(meta.model_dump())

    def test_nested_model_serialization(self):
        """Test nested model serialization."""
        import json

        aphasia = AphasiaReport(is_aphasic=True, severity=0.4)
        step = PipelineStepResult(
            name="test",
            status="ok",
            raw_text="in",
            final_text="out",
        )
        meta = PipelineMetadata(
            pipeline=[step],
            aphasia_report=aphasia,
            total_steps=1,
            successful_steps=1,
        )

        # Should serialize fully nested structure
        json_str = json.dumps(meta.model_dump())
        parsed = json.loads(json_str)
        assert parsed["aphasia_report"]["is_aphasic"] is True
        assert len(parsed["pipeline"]) == 1


class TestSpeechModelEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_aphasia_report_empty_patterns_list(self):
        """Test AphasiaReport with empty patterns list."""
        report = AphasiaReport(is_aphasic=True, severity=0.5, patterns_detected=[])
        assert report.is_aphasic is True
        assert report.patterns_detected == []

    def test_pipeline_step_result_empty_strings(self):
        """Test PipelineStepResult with empty text strings."""
        step = PipelineStepResult(
            name="test",
            status="ok",
            raw_text="",
            final_text="",
        )
        assert step.raw_text == ""
        assert step.final_text == ""

    def test_pipeline_metadata_empty_pipeline(self):
        """Test PipelineMetadata with empty pipeline steps."""
        meta = PipelineMetadata(pipeline=[])
        assert meta.pipeline == []

    def test_from_dict_compatibility(self):
        """Test creating models from dictionaries."""
        # AphasiaReport
        aphasia_dict = {"is_aphasic": True, "severity": 0.5}
        aphasia = AphasiaReport(**aphasia_dict)
        assert aphasia.is_aphasic is True

        # PipelineStepResult
        step_dict = {
            "name": "test",
            "status": "ok",
            "raw_text": "in",
            "final_text": "out",
        }
        step = PipelineStepResult(**step_dict)
        assert step.name == "test"

        # PipelineMetadata
        meta_dict = {
            "pipeline": [],
            "total_steps": 0,
        }
        meta = PipelineMetadata(**meta_dict)
        assert meta.total_steps == 0
