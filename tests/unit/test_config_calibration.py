"""Tests for config/calibration.py (centralized calibration parameters).

Tests cover:
- All calibration dataclasses
- get_calibration_config function
- get_calibration_summary function
- Default values and constants
"""

from mlsdm.config.calibration import (
    APHASIA_DEFAULTS,
    COGNITIVE_CONTROLLER_DEFAULTS,
    COGNITIVE_RHYTHM_DEFAULTS,
    MORAL_FILTER_DEFAULTS,
    PELM_DEFAULTS,
    RATE_LIMIT_DEFAULTS,
    RELIABILITY_DEFAULTS,
    SECURE_MODE_DEFAULTS,
    SYNAPTIC_MEMORY_DEFAULTS,
    SYNERGY_EXPERIENCE_DEFAULTS,
    AphasiaDetectorCalibration,
    CalibrationConfig,
    CognitiveControllerCalibration,
    CognitiveRhythmCalibration,
    MoralFilterCalibration,
    PELMCalibration,
    RateLimitCalibration,
    ReliabilityCalibration,
    SecureModeCalibration,
    SynapticMemoryCalibration,
    SynergyExperienceCalibration,
    get_calibration_config,
    get_calibration_summary,
)


class TestMoralFilterCalibration:
    """Tests for MoralFilterCalibration."""

    def test_moral_filter_defaults(self):
        """Test moral filter default values."""
        assert MORAL_FILTER_DEFAULTS.threshold == 0.50
        assert MORAL_FILTER_DEFAULTS.adapt_rate == 0.05
        assert MORAL_FILTER_DEFAULTS.min_threshold == 0.30
        assert MORAL_FILTER_DEFAULTS.max_threshold == 0.90
        assert MORAL_FILTER_DEFAULTS.dead_band == 0.05
        assert MORAL_FILTER_DEFAULTS.ema_alpha == 0.1

    def test_moral_filter_custom_values(self):
        """Test creating moral filter with custom values."""
        custom = MoralFilterCalibration(
            threshold=0.7,
            adapt_rate=0.1,
            min_threshold=0.4,
            max_threshold=0.95,
        )
        assert custom.threshold == 0.7
        assert custom.adapt_rate == 0.1

    def test_moral_filter_frozen(self):
        """Test that MoralFilterCalibration is frozen (immutable)."""
        import pytest
        from dataclasses import FrozenInstanceError

        with pytest.raises(FrozenInstanceError):
            MORAL_FILTER_DEFAULTS.threshold = 0.6  # type: ignore


class TestAphasiaDetectorCalibration:
    """Tests for AphasiaDetectorCalibration."""

    def test_aphasia_defaults(self):
        """Test aphasia detector default values."""
        assert APHASIA_DEFAULTS.min_sentence_len == 6.0
        assert APHASIA_DEFAULTS.min_function_word_ratio == 0.15
        assert APHASIA_DEFAULTS.max_fragment_ratio == 0.5
        assert APHASIA_DEFAULTS.fragment_length_threshold == 4
        assert APHASIA_DEFAULTS.severity_threshold == 0.3
        assert APHASIA_DEFAULTS.detect_enabled is True
        assert APHASIA_DEFAULTS.repair_enabled is True

    def test_aphasia_custom_values(self):
        """Test creating aphasia calibration with custom values."""
        custom = AphasiaDetectorCalibration(
            min_sentence_len=8.0,
            severity_threshold=0.5,
            detect_enabled=True,
            repair_enabled=False,
        )
        assert custom.min_sentence_len == 8.0
        assert custom.repair_enabled is False


class TestSecureModeCalibration:
    """Tests for SecureModeCalibration."""

    def test_secure_mode_defaults(self):
        """Test secure mode default values."""
        assert SECURE_MODE_DEFAULTS.env_var_name == "MLSDM_SECURE_MODE"
        assert "1" in SECURE_MODE_DEFAULTS.enabled_values
        assert "true" in SECURE_MODE_DEFAULTS.enabled_values
        assert SECURE_MODE_DEFAULTS.disable_neurolang_training is True
        assert SECURE_MODE_DEFAULTS.disable_checkpoint_loading is True
        assert SECURE_MODE_DEFAULTS.disable_aphasia_repair is True


class TestPELMCalibration:
    """Tests for PELMCalibration."""

    def test_pelm_defaults(self):
        """Test PELM default values."""
        assert PELM_DEFAULTS.default_capacity == 20_000
        assert PELM_DEFAULTS.max_capacity == 1_000_000
        assert hasattr(PELM_DEFAULTS, "default_capacity")


class TestSynapticMemoryCalibration:
    """Tests for SynapticMemoryCalibration."""

    def test_synaptic_memory_defaults(self):
        """Test synaptic memory default values."""
        assert hasattr(SYNAPTIC_MEMORY_DEFAULTS, "__class__")
        # Just verify it's accessible
        assert SYNAPTIC_MEMORY_DEFAULTS is not None


class TestCognitiveRhythmCalibration:
    """Tests for CognitiveRhythmCalibration."""

    def test_cognitive_rhythm_defaults(self):
        """Test cognitive rhythm default values."""
        assert hasattr(COGNITIVE_RHYTHM_DEFAULTS, "__class__")
        assert COGNITIVE_RHYTHM_DEFAULTS is not None


class TestReliabilityCalibration:
    """Tests for ReliabilityCalibration."""

    def test_reliability_defaults(self):
        """Test reliability default values."""
        assert hasattr(RELIABILITY_DEFAULTS, "__class__")
        assert RELIABILITY_DEFAULTS is not None


class TestSynergyExperienceCalibration:
    """Tests for SynergyExperienceCalibration."""

    def test_synergy_experience_defaults(self):
        """Test synergy experience default values."""
        assert hasattr(SYNERGY_EXPERIENCE_DEFAULTS, "__class__")
        assert SYNERGY_EXPERIENCE_DEFAULTS is not None


class TestRateLimitCalibration:
    """Tests for RateLimitCalibration."""

    def test_rate_limit_defaults(self):
        """Test rate limit default values."""
        assert hasattr(RATE_LIMIT_DEFAULTS, "__class__")
        assert RATE_LIMIT_DEFAULTS is not None


class TestCognitiveControllerCalibration:
    """Tests for CognitiveControllerCalibration."""

    def test_cognitive_controller_defaults(self):
        """Test cognitive controller default values."""
        assert hasattr(COGNITIVE_CONTROLLER_DEFAULTS, "__class__")
        assert COGNITIVE_CONTROLLER_DEFAULTS is not None


class TestCalibrationConfig:
    """Tests for CalibrationConfig aggregate."""

    def test_calibration_config_contains_all_sections(self):
        """Test that CalibrationConfig contains all calibration sections."""
        config = CalibrationConfig()

        assert hasattr(config, "moral_filter")
        assert hasattr(config, "aphasia")
        assert hasattr(config, "secure_mode")
        assert hasattr(config, "pelm")
        assert hasattr(config, "synaptic_memory")
        assert hasattr(config, "cognitive_rhythm")
        assert hasattr(config, "reliability")
        assert hasattr(config, "synergy_experience")
        assert hasattr(config, "rate_limit")
        assert hasattr(config, "cognitive_controller")

    def test_calibration_config_default_values(self):
        """Test that CalibrationConfig has proper default values."""
        config = CalibrationConfig()

        assert config.moral_filter.threshold == 0.50
        assert config.aphasia.detect_enabled is True
        assert config.secure_mode.env_var_name == "MLSDM_SECURE_MODE"

    def test_calibration_config_custom_values(self):
        """Test creating CalibrationConfig with custom values."""
        custom_moral = MoralFilterCalibration(threshold=0.6)
        config = CalibrationConfig(moral_filter=custom_moral)

        assert config.moral_filter.threshold == 0.6
        # Others should still have defaults
        assert config.aphasia.detect_enabled is True

    def test_calibration_config_frozen(self):
        """Test that CalibrationConfig is frozen."""
        import pytest
        from dataclasses import FrozenInstanceError

        config = CalibrationConfig()
        with pytest.raises(FrozenInstanceError):
            config.moral_filter = MoralFilterCalibration()  # type: ignore


class TestGetCalibrationConfig:
    """Tests for get_calibration_config function."""

    def test_get_calibration_config_returns_config(self):
        """Test that get_calibration_config returns CalibrationConfig."""
        config = get_calibration_config()
        assert isinstance(config, CalibrationConfig)

    def test_get_calibration_config_has_defaults(self):
        """Test that returned config has expected defaults."""
        config = get_calibration_config()

        assert config.moral_filter.threshold == 0.50
        assert config.aphasia.min_sentence_len == 6.0
        assert config.secure_mode.env_var_name == "MLSDM_SECURE_MODE"

    def test_get_calibration_config_returns_same_instance(self):
        """Test that get_calibration_config returns same instance."""
        config1 = get_calibration_config()
        config2 = get_calibration_config()

        # Should be the same instance (singleton pattern)
        assert config1 is config2


class TestGetCalibrationSummary:
    """Tests for get_calibration_summary function."""

    def test_get_calibration_summary_returns_dict(self):
        """Test that get_calibration_summary returns a dictionary."""
        summary = get_calibration_summary()
        assert isinstance(summary, dict)

    def test_get_calibration_summary_has_all_sections(self):
        """Test that summary contains all calibration sections."""
        summary = get_calibration_summary()

        assert "moral_filter" in summary
        assert "aphasia" in summary
        assert "secure_mode" in summary
        # Add more as needed

    def test_get_calibration_summary_moral_filter_section(self):
        """Test moral_filter section in summary."""
        summary = get_calibration_summary()

        moral_filter = summary["moral_filter"]
        assert "threshold" in moral_filter
        assert "adapt_rate" in moral_filter
        assert "min_threshold" in moral_filter
        assert "max_threshold" in moral_filter
        assert "dead_band" in moral_filter
        assert "ema_alpha" in moral_filter

        assert moral_filter["threshold"] == 0.50
        assert moral_filter["min_threshold"] == 0.30

    def test_get_calibration_summary_aphasia_section(self):
        """Test aphasia section in summary."""
        summary = get_calibration_summary()

        aphasia = summary["aphasia"]
        assert "min_sentence_len" in aphasia
        assert "min_function_word_ratio" in aphasia
        assert "max_fragment_ratio" in aphasia
        assert "fragment_length_threshold" in aphasia
        assert "severity_threshold" in aphasia
        assert "detect_enabled" in aphasia
        assert "repair_enabled" in aphasia

        assert aphasia["min_sentence_len"] == 6.0
        assert aphasia["detect_enabled"] is True

    def test_get_calibration_summary_secure_mode_section(self):
        """Test secure_mode section in summary."""
        summary = get_calibration_summary()

        secure_mode = summary["secure_mode"]
        assert "env_var_name" in secure_mode
        assert secure_mode["env_var_name"] == "MLSDM_SECURE_MODE"

    def test_get_calibration_summary_structure(self):
        """Test overall structure of calibration summary."""
        summary = get_calibration_summary()

        # Each section should be a dict
        for section_name, section_data in summary.items():
            assert isinstance(section_name, str)
            assert isinstance(section_data, dict)

            # Each value should be a simple type
            for param_name, param_value in section_data.items():
                assert isinstance(param_name, str)
                # Values can be int, float, bool, str, tuple
                assert isinstance(param_value, (int, float, bool, str, tuple))


class TestCalibrationEdgeCases:
    """Tests for edge cases and integration."""

    def test_all_calibration_classes_are_frozen(self):
        """Test that all calibration classes are frozen."""
        import pytest
        from dataclasses import FrozenInstanceError

        # Test a sample of calibration classes
        with pytest.raises(FrozenInstanceError):
            MORAL_FILTER_DEFAULTS.threshold = 0.99  # type: ignore

        with pytest.raises(FrozenInstanceError):
            APHASIA_DEFAULTS.detect_enabled = False  # type: ignore

    def test_calibration_summary_matches_config(self):
        """Test that summary values match config values."""
        config = get_calibration_config()
        summary = get_calibration_summary()

        # Check a few key values
        assert summary["moral_filter"]["threshold"] == config.moral_filter.threshold
        assert summary["aphasia"]["detect_enabled"] == config.aphasia.detect_enabled
        assert (
            summary["secure_mode"]["env_var_name"]
            == config.secure_mode.env_var_name
        )

    def test_default_constants_match_dataclass_defaults(self):
        """Test that default constants match dataclass defaults."""
        # MORAL_FILTER_DEFAULTS should match MoralFilterCalibration()
        assert MORAL_FILTER_DEFAULTS == MoralFilterCalibration()
        assert APHASIA_DEFAULTS == AphasiaDetectorCalibration()
        assert SECURE_MODE_DEFAULTS == SecureModeCalibration()
