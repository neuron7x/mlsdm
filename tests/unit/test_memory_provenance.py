"""Unit tests for Memory Provenance System.

Tests the AI safety features for tracking memory origin and confidence
to prevent hallucination propagation in PELM.

Resolves: TD-003 (HIGH priority - AI Safety critical)
"""

from datetime import datetime

import numpy as np
import pytest

from mlsdm.memory.phase_entangled_lattice_memory import PhaseEntangledLatticeMemory
from mlsdm.memory.provenance import (
    MemoryProvenance,
    MemorySource,
    compute_sha256_hex,
    get_policy_hash,
)


def _vector_hash(vector: list[float]) -> str:
    return compute_sha256_hex(np.array(vector, dtype=np.float32).tobytes())


def _build_provenance(
    *,
    source: MemorySource,
    confidence: float,
    timestamp: datetime,
    content_hash: str,
    source_id: str = "test-source",
    ingestion_path: str = "tests.unit.memory_provenance",
    trust_tier: int = 3,
    llm_model: str | None = None,
    parent_id: str | None = None,
) -> MemoryProvenance:
    return MemoryProvenance(
        source=source,
        confidence=confidence,
        timestamp=timestamp,
        source_id=source_id,
        ingestion_path=ingestion_path,
        content_hash=content_hash,
        policy_hash=get_policy_hash(),
        trust_tier=trust_tier,
        llm_model=llm_model,
        parent_id=parent_id,
    )


class TestMemoryProvenanceDataModel:
    """Test the provenance data model."""

    def test_provenance_creation(self):
        """Test creating a MemoryProvenance instance."""
        prov = _build_provenance(
            source=MemorySource.USER_INPUT,
            confidence=0.95,
            timestamp=datetime.now(),
            content_hash=compute_sha256_hex(b"memory"),
        )

        assert prov.source == MemorySource.USER_INPUT
        assert prov.confidence == 0.95
        assert prov.llm_model is None
        assert prov.parent_id is None

    def test_provenance_confidence_validation(self):
        """Test confidence must be in [0.0, 1.0] range."""
        # Valid confidence values
        _build_provenance(
            source=MemorySource.USER_INPUT,
            confidence=0.0,
            timestamp=datetime.now(),
            content_hash=compute_sha256_hex(b"low"),
        )
        _build_provenance(
            source=MemorySource.USER_INPUT,
            confidence=1.0,
            timestamp=datetime.now(),
            content_hash=compute_sha256_hex(b"high"),
        )

        # Invalid confidence values
        with pytest.raises(ValueError, match="Confidence must be in range"):
            _build_provenance(
                source=MemorySource.USER_INPUT,
                confidence=1.5,
                timestamp=datetime.now(),
                content_hash=compute_sha256_hex(b"bad1"),
            )

        with pytest.raises(ValueError, match="Confidence must be in range"):
            _build_provenance(
                source=MemorySource.USER_INPUT,
                confidence=-0.1,
                timestamp=datetime.now(),
                content_hash=compute_sha256_hex(b"bad2"),
            )

    def test_is_high_confidence_property(self):
        """Test is_high_confidence property."""
        high_conf = _build_provenance(
            source=MemorySource.USER_INPUT,
            confidence=0.8,
            timestamp=datetime.now(),
            content_hash=compute_sha256_hex(b"high-confidence"),
        )
        assert high_conf.is_high_confidence is True

        low_conf = _build_provenance(
            source=MemorySource.LLM_GENERATION,
            confidence=0.5,
            timestamp=datetime.now(),
            content_hash=compute_sha256_hex(b"low-confidence"),
        )
        assert low_conf.is_high_confidence is False

    def test_is_llm_generated_property(self):
        """Test is_llm_generated property."""
        llm_prov = _build_provenance(
            source=MemorySource.LLM_GENERATION,
            confidence=0.6,
            timestamp=datetime.now(),
            content_hash=compute_sha256_hex(b"llm"),
            llm_model="gpt-4",
        )
        assert llm_prov.is_llm_generated is True

        user_prov = _build_provenance(
            source=MemorySource.USER_INPUT,
            confidence=0.9,
            timestamp=datetime.now(),
            content_hash=compute_sha256_hex(b"user"),
        )
        assert user_prov.is_llm_generated is False


class TestPELMProvenanceStorage:
    """Test PELM provenance storage capabilities."""

    def test_store_with_high_confidence(self):
        """High confidence memories should be stored successfully."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)

        vector = np.random.randn(16).astype(np.float32).tolist()
        provenance = _build_provenance(
            source=MemorySource.USER_INPUT,
            confidence=0.9,
            timestamp=datetime.now(),
            content_hash=_vector_hash(vector),
        )

        idx = pelm.entangle(vector, phase=0.5, provenance=provenance)

        assert idx >= 0  # Successfully stored (not -1)
        assert pelm.size == 1
        assert len(pelm._provenance) == 1
        assert pelm._provenance[0].confidence == 0.9

    def test_reject_low_confidence(self):
        """Low confidence memories should be rejected."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)
        pelm._confidence_threshold = 0.5

        vector = np.random.randn(16).astype(np.float32).tolist()
        provenance = _build_provenance(
            source=MemorySource.LLM_GENERATION,
            confidence=0.3,  # Below threshold
            timestamp=datetime.now(),
            content_hash=_vector_hash(vector),
            trust_tier=1,
        )

        idx = pelm.entangle(vector, phase=0.5, provenance=provenance)

        assert idx == -1  # Rejected
        assert pelm.size == 0

    def test_reject_missing_provenance(self):
        """Missing provenance should be rejected."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)

        vector = np.random.randn(16).astype(np.float32).tolist()

        with pytest.raises(ValueError, match="provenance is required"):
            pelm.entangle(vector, phase=0.5)


class TestPELMProvenanceRetrieval:
    """Test PELM retrieval with confidence filtering."""

    def test_retrieve_filters_by_confidence(self):
        """Retrieval should filter out low-confidence memories."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)
        # Lower the threshold so both can be stored
        pelm._confidence_threshold = 0.3

        # Store high confidence memory
        vector_high = np.random.randn(16).astype(np.float32).tolist()
        pelm.entangle(
            vector_high,
            phase=0.5,
            provenance=_build_provenance(
                source=MemorySource.USER_INPUT,
                confidence=0.9,
                timestamp=datetime.now(),
                content_hash=_vector_hash(vector_high),
            ),
        )

        # Store low confidence memory
        vector_low = np.random.randn(16).astype(np.float32).tolist()
        pelm.entangle(
            vector_low,
            phase=0.5,
            provenance=_build_provenance(
                source=MemorySource.LLM_GENERATION,
                confidence=0.4,
                timestamp=datetime.now(),
                content_hash=_vector_hash(vector_low),
                trust_tier=1,
            ),
        )

        assert pelm.size == 2  # Both stored

        # Retrieve with min_confidence=0.5 (should filter out 0.4)
        query = np.random.randn(16).astype(np.float32).tolist()
        results = pelm.retrieve(query, current_phase=0.5, top_k=10, min_confidence=0.5)

        # Only high-confidence memory should be returned
        assert len(results) == 1
        assert results[0].provenance.confidence >= 0.5

    def test_retrieve_returns_provenance(self):
        """Retrieved memories should include provenance metadata."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)

        vector = np.random.randn(16).astype(np.float32).tolist()
        provenance = _build_provenance(
            source=MemorySource.USER_INPUT,
            confidence=0.95,
            timestamp=datetime.now(),
            content_hash=_vector_hash(vector),
        )

        pelm.entangle(vector, phase=0.5, provenance=provenance)

        query = np.random.randn(16).astype(np.float32).tolist()
        results = pelm.retrieve(query, current_phase=0.5, top_k=1)

        assert len(results) == 1
        assert hasattr(results[0], "provenance")
        assert hasattr(results[0], "memory_id")
        assert results[0].provenance.source == MemorySource.USER_INPUT
        assert results[0].provenance.confidence == 0.95
        assert results[0].provenance.source_id
        assert results[0].provenance.ingestion_path
        assert results[0].provenance.content_hash
        assert results[0].provenance.policy_hash
        assert results[0].provenance.trust_tier >= 0

    def test_retrieve_with_zero_min_confidence(self):
        """With min_confidence=0.0, all memories should be retrieved."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)
        # Lower threshold to allow all to be stored
        pelm._confidence_threshold = 0.0

        # Store memories with varying confidence
        for conf in [0.3, 0.5, 0.9]:
            vector = np.random.randn(16).astype(np.float32).tolist()
            pelm.entangle(
                vector,
                phase=0.5,
                provenance=_build_provenance(
                    source=MemorySource.USER_INPUT,
                    confidence=conf,
                    timestamp=datetime.now(),
                    content_hash=_vector_hash(vector),
                ),
            )

        query = np.random.randn(16).astype(np.float32).tolist()
        results = pelm.retrieve(query, current_phase=0.5, top_k=10, min_confidence=0.0)

        # All memories should be returned (subject to phase tolerance)
        assert len(results) == 3


class TestPELMConfidenceBasedEviction:
    """Test confidence-based eviction when PELM reaches capacity."""

    def test_evict_lowest_confidence(self):
        """When full, should evict the lowest confidence memory."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=3)

        # Fill to capacity with varying confidence
        confidences = [0.9, 0.7, 0.5]
        for conf in confidences:
            vector = np.random.randn(16).astype(np.float32).tolist()
            pelm.entangle(
                vector,
                phase=0.5,
                provenance=_build_provenance(
                    source=MemorySource.USER_INPUT,
                    confidence=conf,
                    timestamp=datetime.now(),
                    content_hash=_vector_hash(vector),
                ),
            )

        assert pelm.size == 3

        # Store one more with high confidence (should evict 0.5)
        vector_new = np.random.randn(16).astype(np.float32).tolist()
        pelm.entangle(
            vector_new,
            phase=0.5,
            provenance=_build_provenance(
                source=MemorySource.USER_INPUT,
                confidence=0.8,
                timestamp=datetime.now(),
                content_hash=_vector_hash(vector_new),
            ),
        )

        # Size should still be 3 (one was evicted)
        assert pelm.size == 3

        # Lowest confidence (0.5) should be gone
        remaining_confidences = [p.confidence for p in pelm._provenance[: pelm.size]]
        assert 0.5 not in remaining_confidences
        assert min(remaining_confidences) >= 0.7

    def test_eviction_maintains_consistency(self):
        """Eviction should maintain consistency across all arrays."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=2)

        # Fill capacity
        for i in range(2):
            vector = np.random.randn(16).astype(np.float32).tolist()
            pelm.entangle(
                vector,
                phase=0.5,
                provenance=_build_provenance(
                    source=MemorySource.USER_INPUT,
                    confidence=0.5 + i * 0.2,  # 0.5, 0.7
                    timestamp=datetime.now(),
                    content_hash=_vector_hash(vector),
                ),
            )

        # Add one more (should evict first with confidence 0.5)
        vector_new = np.random.randn(16).astype(np.float32).tolist()
        pelm.entangle(
            vector_new,
            phase=0.5,
            provenance=_build_provenance(
                source=MemorySource.USER_INPUT,
                confidence=0.9,
                timestamp=datetime.now(),
                content_hash=_vector_hash(vector_new),
            ),
        )

        # Verify consistency
        assert pelm.size == 2
        assert len(pelm._provenance) == 2
        assert len(pelm._memory_ids) == 2

        # Verify retrieval still works
        query = np.random.randn(16).astype(np.float32).tolist()
        results = pelm.retrieve(query, current_phase=0.5, top_k=10)
        assert len(results) <= 2


class TestPELMBatchProvenance:
    """Test batch operations with provenance."""

    def test_entangle_batch_with_provenance(self):
        """Batch entangle should support provenance."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)

        vectors = [np.random.randn(16).astype(np.float32).tolist() for _ in range(3)]
        phases = [0.5, 0.5, 0.5]
        provenances = [
            _build_provenance(
                source=MemorySource.USER_INPUT,
                confidence=0.9,
                timestamp=datetime.now(),
                content_hash=_vector_hash(vector),
            )
            for vector in vectors
        ]

        indices = pelm.entangle_batch(vectors, phases, provenances=provenances)

        assert len(indices) == 3
        assert all(idx >= 0 for idx in indices)
        assert pelm.size == 3
        assert all(p.confidence == 0.9 for p in pelm._provenance[: pelm.size])

    def test_entangle_batch_rejects_low_confidence(self):
        """Batch entangle should reject low confidence memories."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)
        pelm._confidence_threshold = 0.5

        vectors = [np.random.randn(16).astype(np.float32).tolist() for _ in range(3)]
        phases = [0.5, 0.5, 0.5]
        provenances = [
            _build_provenance(
                source=MemorySource.USER_INPUT,
                confidence=conf,
                timestamp=datetime.now(),
                content_hash=_vector_hash(vector),
            )
            for vector, conf in zip(vectors, [0.9, 0.3, 0.7], strict=True)
        ]

        indices = pelm.entangle_batch(vectors, phases, provenances=provenances)

        assert len(indices) == 3
        assert indices[0] >= 0  # Accepted
        assert indices[1] == -1  # Rejected
        assert indices[2] >= 0  # Accepted
        assert pelm.size == 2  # Only 2 stored

    def test_entangle_batch_without_provenance(self):
        """Batch entangle should reject missing provenance."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)

        vectors = [np.random.randn(16).astype(np.float32).tolist() for _ in range(2)]
        phases = [0.5, 0.5]

        with pytest.raises(ValueError, match="provenances are required"):
            pelm.entangle_batch(vectors, phases)


class TestBackwardCompatibility:
    """Test backward compatibility with existing PELM usage."""

    def test_entangle_without_provenance_rejected(self):
        """Existing code without provenance parameter should be rejected."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)

        vector = np.random.randn(16).astype(np.float32).tolist()
        with pytest.raises(ValueError, match="provenance is required"):
            pelm.entangle(vector, phase=0.5)

    def test_retrieve_without_min_confidence_still_works(self):
        """Existing retrieval code should work with default min_confidence=0.0."""
        pelm = PhaseEntangledLatticeMemory(dimension=16, capacity=10)

        vector = np.random.randn(16).astype(np.float32).tolist()
        pelm.entangle(
            vector,
            phase=0.5,
            provenance=_build_provenance(
                source=MemorySource.USER_INPUT,
                confidence=0.9,
                timestamp=datetime.now(),
                content_hash=_vector_hash(vector),
            ),
        )

        query = np.random.randn(16).astype(np.float32).tolist()
        results = pelm.retrieve(query, current_phase=0.5)

        assert len(results) >= 0  # Should work
        # Results should include provenance fields
        if len(results) > 0:
            assert hasattr(results[0], "provenance")
            assert hasattr(results[0], "memory_id")
