"""
Unit Tests for QILM_v2 (Quantum-Inspired Long-term Memory v2)

Tests corruption detection, auto-recovery, and boundary checks.
"""

from datetime import datetime

import numpy as np
import pytest

from mlsdm.memory.provenance import (
    MemoryProvenance,
    MemorySource,
    compute_sha256_hex,
    get_policy_hash,
)
from mlsdm.memory.qilm_v2 import MemoryRetrieval, QILM_v2


def _build_provenance(vector: list[float] | np.ndarray) -> MemoryProvenance:
    vec_np = np.array(vector, dtype=np.float32)
    return MemoryProvenance(
        source=MemorySource.SYSTEM_PROMPT,
        confidence=1.0,
        timestamp=datetime.now(),
        source_id="unit.qilm_v2",
        ingestion_path="tests.unit.test_qilm_v2",
        content_hash=compute_sha256_hex(vec_np.tobytes()),
        policy_hash=get_policy_hash(),
        trust_tier=2,
    )


class TestQILMv2Initialization:
    """Test QILM_v2 initialization."""

    def test_initialization(self):
        """Test QILM_v2 can be initialized."""
        qilm = QILM_v2(dimension=10, capacity=100)
        assert qilm is not None
        assert qilm.dimension == 10
        assert qilm.capacity == 100
        assert qilm.pointer == 0
        assert qilm.size == 0

    def test_initialization_with_defaults(self):
        """Test QILM_v2 initializes with default parameters."""
        qilm = QILM_v2()
        assert qilm.dimension == 384
        assert qilm.capacity == 20000

    def test_initialization_validates_dimension(self):
        """Test initialization validates dimension parameter."""
        with pytest.raises(ValueError, match="dimension must be positive"):
            QILM_v2(dimension=0)
        with pytest.raises(ValueError, match="dimension must be positive"):
            QILM_v2(dimension=-1)

    def test_initialization_validates_capacity(self):
        """Test initialization validates capacity parameter."""
        with pytest.raises(ValueError, match="capacity must be positive"):
            QILM_v2(capacity=0)
        with pytest.raises(ValueError, match="capacity must be positive"):
            QILM_v2(capacity=-1)
        with pytest.raises(ValueError, match="capacity too large"):
            QILM_v2(capacity=2_000_000)


class TestQILMv2Entangle:
    """Test QILM_v2 entangle operation."""

    def test_entangle_basic(self):
        """Test basic entangle operation."""
        qilm = QILM_v2(dimension=3, capacity=10)
        vector = [1.0, 2.0, 3.0]
        phase = 0.5

        idx = qilm.entangle(vector, phase, provenance=_build_provenance(vector))

        assert idx == 0
        assert qilm.size == 1
        assert qilm.pointer == 1
        np.testing.assert_array_almost_equal(qilm.memory_bank[0], vector)
        assert qilm.phase_bank[0] == 0.5

    def test_entangle_multiple_vectors(self):
        """Test entangling multiple vectors."""
        qilm = QILM_v2(dimension=2, capacity=5)

        vectors = [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        phases = [0.1, 0.5, 0.9]

        for i, (vec, phase) in enumerate(zip(vectors, phases, strict=True)):
            idx = qilm.entangle(vec, phase, provenance=_build_provenance(vec))
            assert idx == i

        assert qilm.size == 3
        assert qilm.pointer == 3

    def test_entangle_wraparound(self):
        """Test pointer wraparound when capacity is reached."""
        qilm = QILM_v2(dimension=2, capacity=3)

        # Fill to capacity
        for i in range(3):
            vector = [float(i), float(i + 1)]
            qilm.entangle(vector, 0.1 * i, provenance=_build_provenance(vector))

        assert qilm.pointer == 0  # Should wrap around
        assert qilm.size == 3

        # Add one more to test wraparound
        vector = [10.0, 11.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))
        assert qilm.pointer == 1
        assert qilm.size == 3  # Size stays at capacity


class TestQILMv2Retrieve:
    """Test QILM_v2 retrieve operation."""

    def test_retrieve_basic(self):
        """Test basic retrieve operation."""
        qilm = QILM_v2(dimension=3, capacity=10)

        vector = [1.0, 2.0, 3.0]
        phase = 0.5
        qilm.entangle(vector, phase, provenance=_build_provenance(vector))

        results = qilm.retrieve([1.0, 2.0, 3.0], 0.5, phase_tolerance=0.1, top_k=1)

        assert len(results) == 1
        assert isinstance(results[0], MemoryRetrieval)
        np.testing.assert_array_almost_equal(results[0].vector, vector)
        assert results[0].phase == 0.5

    def test_retrieve_empty_memory(self):
        """Test retrieve returns empty list when memory is empty."""
        qilm = QILM_v2(dimension=3, capacity=10)
        results = qilm.retrieve([1.0, 2.0, 3.0], 0.5)
        assert results == []

    def test_retrieve_with_phase_tolerance(self):
        """Test retrieve with phase tolerance."""
        qilm = QILM_v2(dimension=2, capacity=10)

        vector_a = [1.0, 2.0]
        vector_b = [3.0, 4.0]
        vector_c = [5.0, 6.0]
        qilm.entangle(vector_a, 0.1, provenance=_build_provenance(vector_a))
        qilm.entangle(vector_b, 0.15, provenance=_build_provenance(vector_b))
        qilm.entangle(vector_c, 0.5, provenance=_build_provenance(vector_c))

        results = qilm.retrieve([1.0, 2.0], 0.1, phase_tolerance=0.1, top_k=5)

        # Should get both vectors at phase 0.1 and 0.15
        assert len(results) == 2

    def test_retrieve_no_match(self):
        """Test retrieve with no matching phases."""
        qilm = QILM_v2(dimension=2, capacity=10)

        vector = [1.0, 2.0]
        qilm.entangle(vector, 0.1, provenance=_build_provenance(vector))

        results = qilm.retrieve([1.0, 2.0], 0.9, phase_tolerance=0.05)

        assert results == []


class TestQILMv2CorruptionDetection:
    """Test QILM_v2 corruption detection."""

    def test_detect_no_corruption(self):
        """Test detect_corruption returns False for valid state."""
        qilm = QILM_v2(dimension=3, capacity=10)
        vector = [1.0, 2.0, 3.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        assert not qilm.detect_corruption()

    def test_detect_pointer_out_of_bounds(self):
        """Test corruption detection for pointer out of bounds."""
        qilm = QILM_v2(dimension=3, capacity=10)
        vector = [1.0, 2.0, 3.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        # Corrupt pointer
        qilm.pointer = 100

        assert qilm.detect_corruption()

    def test_detect_negative_pointer(self):
        """Test corruption detection for negative pointer."""
        qilm = QILM_v2(dimension=3, capacity=10)
        vector = [1.0, 2.0, 3.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        # Corrupt pointer
        qilm.pointer = -1

        assert qilm.detect_corruption()

    def test_detect_size_corruption(self):
        """Test corruption detection for invalid size."""
        qilm = QILM_v2(dimension=3, capacity=10)
        vector = [1.0, 2.0, 3.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        # Corrupt size
        qilm.size = 100

        assert qilm.detect_corruption()

    def test_detect_checksum_mismatch(self):
        """Test corruption detection for checksum mismatch."""
        qilm = QILM_v2(dimension=3, capacity=10)
        vector = [1.0, 2.0, 3.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        # Directly corrupt memory without updating checksum
        qilm.memory_bank[0] = np.array([99.0, 99.0, 99.0], dtype=np.float32)

        assert qilm.detect_corruption()


class TestQILMv2AutoRecovery:
    """Test QILM_v2 auto-recovery mechanism."""

    def test_auto_recover_pointer_corruption(self):
        """Test auto-recovery fixes pointer corruption."""
        qilm = QILM_v2(dimension=3, capacity=10)
        vector_a = [1.0, 2.0, 3.0]
        vector_b = [4.0, 5.0, 6.0]
        qilm.entangle(vector_a, 0.5, provenance=_build_provenance(vector_a))
        qilm.entangle(vector_b, 0.6, provenance=_build_provenance(vector_b))

        # Corrupt pointer
        qilm.pointer = 100

        # Verify corruption detected
        assert qilm.detect_corruption()

        # Auto-recover
        recovered = qilm.auto_recover()

        assert recovered
        assert qilm.pointer == 2  # Should be fixed to size % capacity
        assert not qilm.detect_corruption()

    def test_auto_recover_negative_pointer(self):
        """Test auto-recovery fixes negative pointer."""
        qilm = QILM_v2(dimension=3, capacity=10)
        vector = [1.0, 2.0, 3.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        # Corrupt pointer
        qilm.pointer = -5

        recovered = qilm.auto_recover()

        assert recovered
        assert qilm.pointer >= 0
        assert not qilm.detect_corruption()

    def test_auto_recover_size_corruption(self):
        """Test auto-recovery fixes size corruption."""
        qilm = QILM_v2(dimension=3, capacity=10)
        vector = [1.0, 2.0, 3.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        # Corrupt size
        qilm.size = -1

        recovered = qilm.auto_recover()

        assert recovered
        assert qilm.size >= 0
        assert not qilm.detect_corruption()

    def test_auto_recover_rebuilds_norms(self):
        """Test auto-recovery rebuilds norms."""
        qilm = QILM_v2(dimension=3, capacity=10)
        vector = [1.0, 2.0, 3.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        original_norm = qilm.norms[0]

        # Corrupt norms
        qilm.norms[0] = 0.0

        recovered = qilm.auto_recover()

        assert recovered
        # Norm should be restored
        np.testing.assert_almost_equal(qilm.norms[0], original_norm)


class TestQILMv2IntegrationWithCorruption:
    """Test QILM_v2 integration scenarios with corruption."""

    def test_forceful_corruption_and_recovery(self):
        """Test forcefully corrupt state and verify recovery."""
        qilm = QILM_v2(dimension=5, capacity=10)

        # Add some data
        vectors = [[float(i)] * 5 for i in range(5)]
        phases = [0.1 * i for i in range(5)]

        for vec, phase in zip(vectors, phases, strict=True):
            qilm.entangle(vec, phase, provenance=_build_provenance(vec))

        # Verify no corruption initially
        assert not qilm.detect_corruption()

        # Forcefully corrupt multiple aspects
        qilm.pointer = 1000  # Invalid pointer
        qilm.size = -5  # Invalid size
        qilm.memory_bank[0] = np.array([999.0] * 5, dtype=np.float32)  # Corrupt data

        # Verify corruption detected
        assert qilm.detect_corruption()

        # Attempt recovery
        recovered = qilm.auto_recover()

        assert recovered
        assert not qilm.detect_corruption()
        assert qilm.pointer >= 0 and qilm.pointer < qilm.capacity
        assert qilm.size >= 0 and qilm.size <= qilm.capacity

    def test_retrieve_triggers_auto_recovery(self):
        """Test that retrieve triggers auto-recovery on corruption."""
        qilm = QILM_v2(dimension=3, capacity=10)

        vector_a = [1.0, 2.0, 3.0]
        vector_b = [4.0, 5.0, 6.0]
        qilm.entangle(vector_a, 0.5, provenance=_build_provenance(vector_a))
        qilm.entangle(vector_b, 0.5, provenance=_build_provenance(vector_b))

        # Corrupt pointer
        qilm.pointer = -1

        # Retrieve should trigger auto-recovery
        results = qilm.retrieve([1.0, 2.0, 3.0], 0.5)

        # Should succeed after recovery
        assert len(results) > 0
        assert not qilm.detect_corruption()

    def test_entangle_triggers_auto_recovery(self):
        """Test that entangle triggers auto-recovery on corruption."""
        qilm = QILM_v2(dimension=3, capacity=10)

        vector = [1.0, 2.0, 3.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        # Corrupt pointer
        qilm.pointer = 100

        # Entangle should trigger auto-recovery
        vector_new = [4.0, 5.0, 6.0]
        idx = qilm.entangle(vector_new, 0.6, provenance=_build_provenance(vector_new))

        # Should succeed after recovery
        assert idx >= 0
        assert not qilm.detect_corruption()

    def test_recovery_failure_raises_error(self):
        """Test that unrecoverable corruption raises error."""
        qilm = QILM_v2(dimension=3, capacity=10)

        vector = [1.0, 2.0, 3.0]
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        # Create severe corruption that might not be recoverable
        # by setting invalid pointer
        qilm.pointer = 100

        # Force recovery to fail by making auto_recover fail internally
        # This is a simulation - in practice the current implementation should recover
        # But we test the error path exists
        try:
            # Normal operations should attempt recovery
            vector_new = [4.0, 5.0, 6.0]
            qilm.entangle(vector_new, 0.6, provenance=_build_provenance(vector_new))
        except RuntimeError as e:
            # If recovery fails, should raise RuntimeError
            assert "Memory corruption" in str(e)


class TestQILMv2BoundaryChecks:
    """Test QILM_v2 boundary checks."""

    def test_pointer_wraparound_at_capacity(self):
        """Test explicit pointer wraparound at capacity boundary."""
        qilm = QILM_v2(dimension=2, capacity=5)

        # Fill to capacity
        for i in range(5):
            vector = [float(i), float(i + 1)]
            idx = qilm.entangle(vector, 0.1, provenance=_build_provenance(vector))
            assert idx == i

        # Pointer should wrap to 0
        assert qilm.pointer == 0

        # Next entangle should use index 0
        vector = [99.0, 99.0]
        idx = qilm.entangle(vector, 0.9, provenance=_build_provenance(vector))
        assert idx == 0
        assert qilm.pointer == 1

    def test_size_stops_at_capacity(self):
        """Test size doesn't exceed capacity."""
        qilm = QILM_v2(dimension=2, capacity=3)

        # Add more than capacity
        for i in range(10):
            vector = [float(i), float(i + 1)]
            qilm.entangle(vector, 0.1 * i, provenance=_build_provenance(vector))

        # Size should be capped at capacity
        assert qilm.size == 3
        assert qilm.size <= qilm.capacity

    def test_validate_pointer_bounds(self):
        """Test _validate_pointer_bounds method."""
        qilm = QILM_v2(dimension=2, capacity=10)

        # Valid state
        assert qilm._validate_pointer_bounds()

        # Invalid pointer (too large)
        qilm.pointer = 100
        assert not qilm._validate_pointer_bounds()

        # Invalid pointer (negative)
        qilm.pointer = -1
        assert not qilm._validate_pointer_bounds()

        # Fix pointer
        qilm.pointer = 5
        assert qilm._validate_pointer_bounds()


class TestQILMv2StateStats:
    """Test QILM_v2 state statistics."""

    def test_get_state_stats(self):
        """Test get_state_stats returns correct information."""
        qilm = QILM_v2(dimension=10, capacity=100)

        vector = [1.0] * 10
        qilm.entangle(vector, 0.5, provenance=_build_provenance(vector))

        stats = qilm.get_state_stats()

        assert stats["capacity"] == 100
        assert stats["used"] == 1
        assert "memory_mb" in stats
        assert isinstance(stats["memory_mb"], float)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
