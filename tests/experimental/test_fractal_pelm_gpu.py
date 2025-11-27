"""Experimental tests for FractalPELMGPU.

These tests are designed to run on CPU to avoid CI GPU requirements.
The tests validate basic functionality without requiring CUDA hardware.
"""

from __future__ import annotations

import numpy as np
import pytest

# Skip all tests in this module if torch is not available
pytest.importorskip("torch")

# Mark all tests in this module as experimental
pytestmark = pytest.mark.experimental


class TestFractalPELMGPUInitialization:
    """Test FractalPELMGPU initialization and validation."""

    def test_initialization_default(self) -> None:
        """Test default initialization with CPU device."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=64, capacity=1000, device="cpu")
        assert memory.dimension == 64
        assert memory.capacity == 1000
        assert memory.size == 0

    def test_initialization_validates_dimension(self) -> None:
        """Test that initialization validates dimension is positive."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        with pytest.raises(ValueError, match="dimension must be positive"):
            FractalPELMGPU(dimension=0, capacity=100, device="cpu")

        with pytest.raises(ValueError, match="dimension must be positive"):
            FractalPELMGPU(dimension=-1, capacity=100, device="cpu")

    def test_initialization_validates_capacity(self) -> None:
        """Test that initialization validates capacity is positive."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        with pytest.raises(ValueError, match="capacity must be positive"):
            FractalPELMGPU(dimension=64, capacity=0, device="cpu")

        with pytest.raises(ValueError, match="capacity must be positive"):
            FractalPELMGPU(dimension=64, capacity=-10, device="cpu")

    def test_amp_disabled_on_cpu(self) -> None:
        """Test that AMP is disabled when using CPU device."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=64, capacity=100, device="cpu", use_amp=True)
        # Even if use_amp=True is passed, it should be False on CPU
        assert memory.use_amp is False


class TestFractalPELMGPUBatchEntangle:
    """Test batch_entangle operation."""

    def test_batch_entangle_basic(self) -> None:
        """Test basic batch entangle with numpy arrays."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=16, capacity=100, device="cpu")

        vectors = np.random.randn(10, 16).astype(np.float32)
        phases = np.random.uniform(0, 1, 10).astype(np.float32)

        memory.batch_entangle(vectors, phases)

        assert memory.size == 10

    def test_batch_entangle_with_metadata(self) -> None:
        """Test batch entangle with metadata."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=8, capacity=50, device="cpu")

        vectors = np.random.randn(5, 8).astype(np.float32)
        phases = np.random.uniform(0, 1, 5).astype(np.float32)
        metadatas = [{"id": i, "label": f"item_{i}"} for i in range(5)]

        memory.batch_entangle(vectors, phases, metadatas)

        assert memory.size == 5

    def test_batch_entangle_dimension_mismatch(self) -> None:
        """Test that dimension mismatch raises ValueError."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=16, capacity=100, device="cpu")

        # Wrong dimension: 32 instead of 16
        vectors = np.random.randn(10, 32).astype(np.float32)
        phases = np.random.uniform(0, 1, 10).astype(np.float32)

        with pytest.raises(ValueError, match="dimension mismatch"):
            memory.batch_entangle(vectors, phases)

    def test_batch_entangle_capacity_overflow(self) -> None:
        """Test that exceeding capacity raises RuntimeError."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=8, capacity=10, device="cpu")

        # Try to add more than capacity
        vectors = np.random.randn(15, 8).astype(np.float32)
        phases = np.random.uniform(0, 1, 15).astype(np.float32)

        with pytest.raises(RuntimeError, match="Capacity exceeded"):
            memory.batch_entangle(vectors, phases)


class TestFractalPELMGPURetrieve:
    """Test retrieve operation."""

    def test_retrieve_empty_memory(self) -> None:
        """Test retrieve on empty memory returns empty list."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=16, capacity=100, device="cpu")

        query = np.random.randn(16).astype(np.float32)
        results = memory.retrieve(query, current_phase=0.5, top_k=5)

        assert results == []

    def test_retrieve_returns_results(self) -> None:
        """Test that retrieve returns non-empty results after entangle."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=16, capacity=100, device="cpu")

        # Add some vectors
        vectors = np.random.randn(20, 16).astype(np.float32)
        phases = np.random.uniform(0, 1, 20).astype(np.float32)
        memory.batch_entangle(vectors, phases)

        # Query with the first vector
        query = vectors[0]
        results = memory.retrieve(query, current_phase=phases[0], top_k=5)

        # Should return up to 5 results
        assert len(results) > 0
        assert len(results) <= 5

        # Verify result structure
        for score, vector, metadata in results:
            assert isinstance(score, float)
            assert isinstance(vector, np.ndarray)
            assert vector.shape == (16,)
            assert vector.dtype == np.float32

    def test_retrieve_query_shape_validation(self) -> None:
        """Test that query shape mismatch raises ValueError."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=16, capacity=100, device="cpu")

        # Wrong shape query
        wrong_query = np.random.randn(32).astype(np.float32)

        with pytest.raises(ValueError, match="shape mismatch"):
            memory.retrieve(wrong_query, current_phase=0.5)

    def test_retrieve_with_metadata(self) -> None:
        """Test that retrieve returns correct metadata."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=8, capacity=50, device="cpu")

        # Create distinct vectors
        vectors = np.eye(8, dtype=np.float32)[:5]  # First 5 identity vectors
        phases = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
        metadatas = [{"id": i} for i in range(5)]

        memory.batch_entangle(vectors, phases, metadatas)

        # Query with first vector
        results = memory.retrieve(vectors[0], current_phase=0.1, top_k=3)

        # Check that metadata is present
        assert len(results) > 0
        # First result should have highest similarity to query
        top_score, top_vector, top_meta = results[0]
        assert top_meta is not None
        assert "id" in top_meta


class TestFractalPELMGPUBatchRetrieve:
    """Test batch_retrieve operation."""

    def test_batch_retrieve_basic(self) -> None:
        """Test basic batch retrieve."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=16, capacity=100, device="cpu")

        # Add vectors
        vectors = np.random.randn(30, 16).astype(np.float32)
        phases = np.random.uniform(0, 1, 30).astype(np.float32)
        memory.batch_entangle(vectors, phases)

        # Batch query
        query_vectors = np.random.randn(5, 16).astype(np.float32)
        query_phases = np.random.uniform(0, 1, 5).astype(np.float32)

        results = memory.batch_retrieve(query_vectors, query_phases, top_k=3)

        # Should return one result list per query
        assert len(results) == 5
        for query_results in results:
            assert len(query_results) <= 3

    def test_batch_retrieve_shape_validation(self) -> None:
        """Test batch retrieve validates shapes."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=16, capacity=100, device="cpu")

        # Wrong dimension
        wrong_queries = np.random.randn(5, 32).astype(np.float32)
        phases = np.random.uniform(0, 1, 5).astype(np.float32)

        with pytest.raises(ValueError, match="dimension mismatch"):
            memory.batch_retrieve(wrong_queries, phases)


class TestFractalPELMGPUReset:
    """Test reset operation."""

    def test_reset_clears_size(self) -> None:
        """Test that reset sets size to 0."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=16, capacity=100, device="cpu")

        # Add some vectors
        vectors = np.random.randn(20, 16).astype(np.float32)
        phases = np.random.uniform(0, 1, 20).astype(np.float32)
        memory.batch_entangle(vectors, phases)

        assert memory.size == 20

        # Reset
        memory.reset()

        assert memory.size == 0
        assert memory.capacity == 100  # Capacity unchanged

    def test_reset_allows_reuse(self) -> None:
        """Test that memory can be reused after reset."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        memory = FractalPELMGPU(dimension=16, capacity=100, device="cpu")

        # Add and reset
        vectors1 = np.random.randn(10, 16).astype(np.float32)
        phases1 = np.random.uniform(0, 1, 10).astype(np.float32)
        memory.batch_entangle(vectors1, phases1)
        memory.reset()

        # Add new vectors
        vectors2 = np.random.randn(15, 16).astype(np.float32)
        phases2 = np.random.uniform(0, 1, 15).astype(np.float32)
        memory.batch_entangle(vectors2, phases2)

        assert memory.size == 15

        # Retrieve should work
        results = memory.retrieve(vectors2[0], current_phase=phases2[0], top_k=5)
        assert len(results) > 0


class TestFractalPELMGPUImport:
    """Test module import behavior."""

    def test_import_from_experimental(self) -> None:
        """Test that FractalPELMGPU can be imported from experimental package."""
        from mlsdm.memory.experimental import FractalPELMGPU

        assert FractalPELMGPU is not None

    def test_import_directly(self) -> None:
        """Test direct import from module."""
        from mlsdm.memory.experimental.fractal_pelm_gpu import FractalPELMGPU

        assert FractalPELMGPU is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
