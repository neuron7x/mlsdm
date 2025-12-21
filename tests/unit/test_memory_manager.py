"""
Comprehensive tests for core/memory_manager.py.

Tests cover:
- MemoryManager initialization
- Sensitive data detection
- Event processing
- Simulation functionality
- State persistence
"""

from collections.abc import Iterator

import numpy as np
import pytest

from mlsdm.core.memory_manager import MemoryManager


class TestMemoryManagerInit:
    """Tests for MemoryManager initialization."""

    def test_default_initialization(self):
        """Test initialization with default config."""
        config = {"dimension": 10}
        manager = MemoryManager(config)

        assert manager.dimension == 10
        assert manager.memory is not None
        assert manager.filter is not None
        assert manager.matcher is not None
        assert manager.rhythm is not None
        assert manager.qilm is not None
        assert manager.metrics_collector is not None
        assert manager.strict_mode is False

    def test_custom_initialization(self):
        """Test initialization with custom config."""
        config = {
            "dimension": 5,
            "multi_level_memory": {
                "lambda_l1": 0.6,
                "lambda_l2": 0.2,
                "lambda_l3": 0.05,
                "theta_l1": 1.5,
                "theta_l2": 2.5,
                "gating12": 0.4,
                "gating23": 0.2,
            },
            "moral_filter": {
                "threshold": 0.6,
                "adapt_rate": 0.1,
                "min_threshold": 0.4,
                "max_threshold": 0.8,
            },
            "cognitive_rhythm": {
                "wake_duration": 10,
                "sleep_duration": 5,
            },
            "strict_mode": True,
        }
        manager = MemoryManager(config)

        assert manager.dimension == 5
        assert manager.strict_mode is True
        assert manager.filter.threshold == 0.6

    def test_ontology_initialization(self):
        """Test ontology matcher initialization with custom vectors."""
        config = {
            "dimension": 3,
            "ontology_matcher": {
                "ontology_vectors": [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
                "ontology_labels": ["cat_a", "cat_b"],
            },
        }
        manager = MemoryManager(config)

        assert manager.matcher is not None
        assert manager.matcher.dimension == 3


class TestSensitiveDetection:
    """Tests for sensitive data detection."""

    def test_is_sensitive_normal_vector(self):
        """Test normal vector is not flagged as sensitive."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        vec = np.array([1.0, 2.0, 3.0])  # norm ~= 3.74, sum = 6
        assert manager._is_sensitive(vec) is False

    def test_is_sensitive_high_norm(self):
        """Test high norm vector is flagged as sensitive."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        vec = np.array([10.0, 10.0, 10.0])  # norm > 10
        assert manager._is_sensitive(vec) is True

    def test_is_sensitive_negative_sum(self):
        """Test negative sum vector is flagged as sensitive."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        vec = np.array([-5.0, -5.0, 1.0])  # sum = -9 < 0
        assert manager._is_sensitive(vec) is True

    def test_is_sensitive_boundary(self):
        """Test boundary conditions."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        # Exactly at norm 10
        vec = np.array([10.0, 0.0, 0.0])
        assert manager._is_sensitive(vec) is False  # norm == 10, not > 10

        # Exactly at sum 0
        vec = np.array([1.0, -1.0, 0.0])
        assert manager._is_sensitive(vec) is False  # sum == 0, not < 0


class TestProcessEvent:
    """Tests for async event processing."""

    @pytest.mark.asyncio
    async def test_process_event_accepted(self):
        """Test processing an accepted event."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        # High moral value should be accepted
        event_vector = np.array([1.0, 0.0, 0.0])
        await manager.process_event(event_vector, moral_value=0.8)

        metrics = manager.metrics_collector.get_metrics()
        assert metrics["accepted_events_count"] == 1
        assert metrics["total_events_processed"] == 1

    @pytest.mark.asyncio
    async def test_process_event_rejected(self):
        """Test processing a rejected event (low moral value)."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        # First we need to initialize with some events to get a baseline
        # Low moral value should be rejected
        event_vector = np.array([1.0, 0.0, 0.0])
        await manager.process_event(event_vector, moral_value=0.1)

        metrics = manager.metrics_collector.get_metrics()
        assert metrics["latent_events_count"] == 1

    @pytest.mark.asyncio
    async def test_process_event_strict_mode_sensitive(self):
        """Test strict mode rejects sensitive data."""
        config = {"dimension": 3, "strict_mode": True}
        manager = MemoryManager(config)

        # Create sensitive vector (high norm)
        event_vector = np.array([10.0, 10.0, 10.0])

        with pytest.raises(ValueError) as exc_info:
            await manager.process_event(event_vector, moral_value=0.8)

        assert "Sensitive data detected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_event_adapts_threshold(self):
        """Test that moral filter adapts based on acceptance rate."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        # Process multiple events
        for _ in range(5):
            await manager.process_event(np.random.randn(3), moral_value=0.7)

        # Threshold should have been adapted
        # (adaptation behavior depends on accept rate)
        assert manager.filter.threshold > 0  # Still valid threshold

    @pytest.mark.asyncio
    async def test_process_event_records_latency(self):
        """Test that event processing records latency."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        await manager.process_event(np.array([1.0, 0.0, 0.0]), moral_value=0.8)

        metrics = manager.metrics_collector.get_metrics()
        assert len(metrics["latencies"]) == 1
        assert metrics["latencies"][0] >= 0


class TestSimulate:
    """Tests for simulate method."""

    @pytest.mark.asyncio
    async def test_simulate_basic(self):
        """Test basic simulation."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        def event_gen() -> Iterator[tuple[np.ndarray, float]]:
            for _ in range(3):
                yield np.array([1.0, 0.0, 0.0]), 0.7

        await manager.simulate(3, event_gen())

        metrics = manager.metrics_collector.get_metrics()
        assert len(metrics["time"]) == 3
        assert len(metrics["phase"]) == 3

    @pytest.mark.asyncio
    async def test_simulate_dimension_mismatch(self):
        """Test simulation rejects dimension mismatched events."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        def event_gen() -> Iterator[tuple[np.ndarray, float]]:
            yield np.array([1.0, 0.0, 0.0, 0.0]), 0.7  # Wrong dimension

        with pytest.raises(ValueError) as exc_info:
            await manager.simulate(1, event_gen())

        assert "dimension mismatch" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_simulate_wake_sleep_cycle(self):
        """Test simulation respects wake/sleep cycle."""
        config = {
            "dimension": 3,
            "cognitive_rhythm": {
                "wake_duration": 2,
                "sleep_duration": 2,
            },
        }
        manager = MemoryManager(config)

        # Event list prepared for potential future use
        _events_processed: list[tuple[np.ndarray, float]] = []

        def event_gen() -> Iterator[tuple[np.ndarray, float]]:
            for i in range(6):
                yield np.array([1.0, 0.0, 0.0]), 0.8

        await manager.simulate(6, event_gen())

        metrics = manager.metrics_collector.get_metrics()
        # Should have phases recorded
        assert len(metrics["phase"]) == 6


class TestRunSimulation:
    """Tests for run_simulation method."""

    def test_run_simulation_with_generator(self):
        """Test run_simulation with custom generator."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        def event_gen() -> Iterator[tuple[np.ndarray, float]]:
            for _ in range(5):
                yield np.array([1.0, 0.0, 0.0]), 0.7

        manager.run_simulation(5, event_gen())

        metrics = manager.metrics_collector.get_metrics()
        assert len(metrics["time"]) == 5

    def test_run_simulation_default_generator(self):
        """Test run_simulation with default generator."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        manager.run_simulation(3)

        metrics = manager.metrics_collector.get_metrics()
        assert len(metrics["time"]) == 3

    def test_run_simulation_records_memory_state(self):
        """Test run_simulation records memory state."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        manager.run_simulation(5)

        metrics = manager.metrics_collector.get_metrics()
        assert len(metrics["L1_norm"]) == 5
        assert len(metrics["L2_norm"]) == 5
        assert len(metrics["L3_norm"]) == 5


class TestStatePersistence:
    """Tests for state save/load functionality."""

    def test_save_system_state(self, tmp_path):
        """Test saving system state includes format_version."""
        import json

        config = {"dimension": 3}
        manager = MemoryManager(config)

        # Process some events
        manager.run_simulation(3)

        filepath = str(tmp_path / "state.json")
        manager.save_system_state(filepath)

        # File should exist
        import os

        assert os.path.exists(filepath)

        # Check saved structure
        with open(filepath) as f:
            data = json.load(f)

        assert "format_version" in data
        assert data["format_version"] == 1
        assert "memory_state" in data
        assert "qilm" in data

    def test_load_system_state_restores_memory(self, tmp_path):
        """Test loading system state restores memory L1/L2/L3."""
        config = {"dimension": 3}
        manager1 = MemoryManager(config)

        # Run simulation to populate memory
        manager1.run_simulation(5)

        # Capture state
        l1_before, l2_before, l3_before = manager1.memory.get_state()

        filepath = str(tmp_path / "state.json")
        manager1.save_system_state(filepath)

        # Create new manager and load state
        manager2 = MemoryManager(config)
        manager2.load_system_state(filepath)

        l1_after, l2_after, l3_after = manager2.memory.get_state()

        # Verify memory state was restored
        np.testing.assert_allclose(l1_before, l1_after, rtol=1e-5)
        np.testing.assert_allclose(l2_before, l2_after, rtol=1e-5)
        np.testing.assert_allclose(l3_before, l3_after, rtol=1e-5)

    def test_load_system_state_restores_memory_params(self, tmp_path):
        """Test loading system state restores memory parameters."""
        config = {
            "dimension": 3,
            "multi_level_memory": {
                "lambda_l1": 0.7,
                "lambda_l2": 0.3,
                "theta_l1": 1.5,
                "gating12": 0.6,
            },
        }
        manager1 = MemoryManager(config)

        filepath = str(tmp_path / "state.json")
        manager1.save_system_state(filepath)

        # Create manager with different params
        config2 = {"dimension": 3}
        manager2 = MemoryManager(config2)

        # Verify params are different before load
        assert manager2.memory.lambda_l1 != 0.7

        # Load state
        manager2.load_system_state(filepath)

        # Verify params were restored
        assert manager2.memory.lambda_l1 == 0.7
        assert manager2.memory.lambda_l2 == 0.3
        assert manager2.memory.theta_l1 == 1.5
        assert manager2.memory.gating12 == 0.6

    def test_load_system_state_restores_qilm(self, tmp_path):
        """Test loading system state restores QILM memory and phases."""
        config = {"dimension": 3}
        manager1 = MemoryManager(config)

        # Run simulation to populate QILM
        manager1.run_simulation(5)

        qilm_memory_count = len(manager1.qilm.memory)
        qilm_phases_count = len(manager1.qilm.phases)

        # Ensure we have some data
        assert qilm_memory_count > 0

        # Get first vector for comparison
        first_vec = manager1.qilm.memory[0].copy()

        filepath = str(tmp_path / "state.json")
        manager1.save_system_state(filepath)

        # Create new manager and load state
        manager2 = MemoryManager(config)
        assert len(manager2.qilm.memory) == 0  # Should be empty before load

        manager2.load_system_state(filepath)

        # Verify QILM was restored
        assert len(manager2.qilm.memory) == qilm_memory_count
        assert len(manager2.qilm.phases) == qilm_phases_count
        np.testing.assert_allclose(manager2.qilm.memory[0], first_vec, rtol=1e-5)

    def test_load_system_state_save_load_invariants(self, tmp_path):
        """Test save -> load -> save produces identical output (invariants equality)."""
        import json

        config = {"dimension": 5}
        manager = MemoryManager(config)
        manager.run_simulation(10)

        filepath1 = str(tmp_path / "state1.json")
        manager.save_system_state(filepath1)

        # Load into same manager
        manager.load_system_state(filepath1)

        # Save again
        filepath2 = str(tmp_path / "state2.json")
        manager.save_system_state(filepath2)

        # Compare outputs
        with open(filepath1) as f:
            data1 = json.load(f)
        with open(filepath2) as f:
            data2 = json.load(f)

        # Should be identical
        assert data1 == data2

    def test_load_system_state_file_not_found(self, tmp_path):
        """Test loading from non-existent file raises StateFileNotFoundError."""
        from mlsdm.utils.errors import StateFileNotFoundError

        config = {"dimension": 3}
        manager = MemoryManager(config)

        with pytest.raises(StateFileNotFoundError) as exc_info:
            manager.load_system_state(str(tmp_path / "nonexistent.json"))

        assert exc_info.value.code.value == "E407"
        assert "nonexistent.json" in str(exc_info.value)

    def test_load_system_state_corrupt_json(self, tmp_path):
        """Test loading corrupt JSON raises StateCorruptError."""
        from mlsdm.utils.errors import StateCorruptError

        config = {"dimension": 3}
        manager = MemoryManager(config)

        filepath = str(tmp_path / "corrupt.json")
        with open(filepath, "w") as f:
            f.write("not valid json {{{")

        with pytest.raises(StateCorruptError) as exc_info:
            manager.load_system_state(filepath)

        assert exc_info.value.code.value == "E408"
        # The error may mention JSONDecodeError directly or through RetryError
        error_str = str(exc_info.value)
        assert "JSONDecodeError" in error_str or "JSON" in error_str

    def test_load_system_state_missing_keys(self, tmp_path):
        """Test loading file with missing keys raises StateIncompleteError."""
        import json

        from mlsdm.utils.errors import StateIncompleteError

        config = {"dimension": 3}
        manager = MemoryManager(config)

        filepath = str(tmp_path / "incomplete.json")
        with open(filepath, "w") as f:
            json.dump({"format_version": 1, "memory_state": {}}, f)

        with pytest.raises(StateIncompleteError) as exc_info:
            manager.load_system_state(filepath)

        assert exc_info.value.code.value == "E410"
        assert "qilm" in str(exc_info.value.error_details.details.get("missing_fields", []))

    def test_load_system_state_version_mismatch(self, tmp_path):
        """Test loading file with future version raises StateVersionMismatchError."""
        import json

        from mlsdm.utils.errors import StateVersionMismatchError

        config = {"dimension": 3}
        manager = MemoryManager(config)

        filepath = str(tmp_path / "future.json")
        with open(filepath, "w") as f:
            json.dump({"format_version": 999, "memory_state": {}, "qilm": {}}, f)

        with pytest.raises(StateVersionMismatchError) as exc_info:
            manager.load_system_state(filepath)

        assert exc_info.value.code.value == "E409"
        assert exc_info.value.error_details.details["file_version"] == 999

    def test_load_system_state_dimension_mismatch(self, tmp_path):
        """Test loading state with different dimension raises StateIncompleteError."""
        from mlsdm.utils.errors import StateIncompleteError

        config1 = {"dimension": 3}
        manager1 = MemoryManager(config1)
        manager1.run_simulation(2)

        filepath = str(tmp_path / "state.json")
        manager1.save_system_state(filepath)

        # Try to load into manager with different dimension
        config2 = {"dimension": 5}
        manager2 = MemoryManager(config2)

        with pytest.raises(StateIncompleteError) as exc_info:
            manager2.load_system_state(filepath)

        assert exc_info.value.code.value == "E410"
        assert "dimension" in str(exc_info.value)

    def test_load_system_state_invalid_field_type(self, tmp_path):
        """Test loading state with invalid field types raises StateIncompleteError."""
        import json

        from mlsdm.utils.errors import StateIncompleteError

        config = {"dimension": 3}
        manager = MemoryManager(config)

        filepath = str(tmp_path / "invalid.json")
        with open(filepath, "w") as f:
            json.dump(
                {
                    "format_version": 1,
                    "memory_state": {
                        "dimension": "not an int",  # Invalid type
                        "lambda_l1": 0.5,
                        "lambda_l2": 0.1,
                        "lambda_l3": 0.01,
                        "theta_l1": 1.0,
                        "theta_l2": 2.0,
                        "gating12": 0.5,
                        "gating23": 0.3,
                        "state_L1": [0.0, 0.0, 0.0],
                        "state_L2": [0.0, 0.0, 0.0],
                        "state_L3": [0.0, 0.0, 0.0],
                    },
                    "qilm": {"memory": [], "phases": []},
                },
                f,
            )

        with pytest.raises(StateIncompleteError) as exc_info:
            manager.load_system_state(filepath)

        assert exc_info.value.code.value == "E410"

    def test_load_system_state_legacy_no_version(self, tmp_path):
        """Test loading legacy state without format_version defaults to version 1."""
        import json

        config = {"dimension": 3}
        manager1 = MemoryManager(config)
        manager1.run_simulation(2)

        filepath = str(tmp_path / "legacy.json")
        manager1.save_system_state(filepath)

        # Remove format_version from saved file (simulate legacy format)
        with open(filepath) as f:
            data = json.load(f)
        del data["format_version"]
        with open(filepath, "w") as f:
            json.dump(data, f)

        # Should load successfully
        manager2 = MemoryManager(config)
        manager2.load_system_state(filepath)

        # Verify state was restored
        l1_1, _, _ = manager1.memory.get_state()
        l1_2, _, _ = manager2.memory.get_state()
        np.testing.assert_allclose(l1_1, l1_2, rtol=1e-5)


class TestMetricsRecording:
    """Tests for metrics recording during operations."""

    def test_metrics_recorded_during_simulation(self):
        """Test all metrics are recorded during simulation."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        manager.run_simulation(5)

        metrics = manager.metrics_collector.get_metrics()

        # Check all metric arrays are populated
        assert len(metrics["time"]) == 5
        assert len(metrics["phase"]) == 5
        assert len(metrics["L1_norm"]) == 5
        assert len(metrics["L2_norm"]) == 5
        assert len(metrics["L3_norm"]) == 5
        assert len(metrics["entropy_L1"]) == 5
        assert len(metrics["entropy_L2"]) == 5
        assert len(metrics["entropy_L3"]) == 5
        assert len(metrics["current_moral_threshold"]) == 5

    def test_moral_threshold_tracked(self):
        """Test moral threshold is tracked over simulation."""
        config = {"dimension": 3}
        manager = MemoryManager(config)

        manager.run_simulation(10)

        metrics = manager.metrics_collector.get_metrics()
        assert len(metrics["current_moral_threshold"]) == 10
        # All thresholds should be valid values
        for threshold in metrics["current_moral_threshold"]:
            assert 0 <= threshold <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
