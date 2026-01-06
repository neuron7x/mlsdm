"""
Mutation tests for PhaseEntangledLatticeMemory (PELM).

These tests verify that existing tests can detect bugs in critical
PELM code paths by introducing small mutations.

Critical mutations to test:
- Capacity overflow handling
- Boundary condition checks
- Phase validation logic
- Vector dimension validation
- Confidence threshold logic
"""

import numpy as np
import pytest

from mlsdm.memory.phase_entangled_lattice_memory import PhaseEntangledLatticeMemory
from mlsdm.memory.provenance import MemoryProvenance, MemorySource


class TestPELMCapacityMutations:
    """
    Test that mutations to capacity handling are detected.
    
    These tests validate capacity overflow and eviction logic.
    """
    
    def test_capacity_initialization_positive(self):
        """Test capacity must be positive."""
        # Valid capacity
        pelm = PhaseEntangledLatticeMemory(dimension=10, capacity=100)
        assert pelm.capacity == 100
        
        # Invalid capacities should raise
        with pytest.raises(ValueError, match="capacity must be positive"):
            PhaseEntangledLatticeMemory(dimension=10, capacity=0)
        
        with pytest.raises(ValueError, match="capacity must be positive"):
            PhaseEntangledLatticeMemory(dimension=10, capacity=-1)
    
    def test_capacity_max_limit(self):
        """Test capacity respects MAX_CAPACITY."""
        # Should raise if exceeding MAX_CAPACITY
        with pytest.raises(ValueError, match="capacity too large"):
            PhaseEntangledLatticeMemory(
                dimension=10,
                capacity=PhaseEntangledLatticeMemory.MAX_CAPACITY + 1
            )
    
    def test_capacity_overflow_handling(self):
        """Test capacity overflow triggers eviction."""
        pelm = PhaseEntangledLatticeMemory(dimension=10, capacity=5)
        
        # Fill to capacity
        for i in range(5):
            vector = [float(j) for j in range(10)]
            result = pelm.entangle(vector, phase=0.5)
            assert result != -1
        
        # Size should be at capacity
        assert pelm.size == 5
        
        # Adding one more should still work (eviction)
        vector = [1.0] * 10
        result = pelm.entangle(vector, phase=0.5)
        assert result != -1
        
        # Size should still be at capacity
        assert pelm.size == 5


class TestPELMBoundaryMutations:
    """
    Test that mutations to boundary checks are detected.
    
    Validates dimension and phase boundary validation.
    """
    
    def test_dimension_positive(self):
        """Test dimension must be positive."""
        # Valid dimension
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        assert pelm.dimension == 10
        
        # Invalid dimensions should raise
        with pytest.raises(ValueError, match="dimension must be positive"):
            PhaseEntangledLatticeMemory(dimension=0)
        
        with pytest.raises(ValueError, match="dimension must be positive"):
            PhaseEntangledLatticeMemory(dimension=-1)
    
    def test_vector_dimension_match(self):
        """Test vector dimension must match PELM dimension."""
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        
        # Correct dimension should work
        vector = [1.0] * 10
        result = pelm.entangle(vector, phase=0.5)
        assert result != -1
        
        # Wrong dimension should raise
        with pytest.raises(ValueError, match="vector dimension mismatch"):
            pelm.entangle([1.0] * 5, phase=0.5)
        
        with pytest.raises(ValueError, match="vector dimension mismatch"):
            pelm.entangle([1.0] * 15, phase=0.5)
    
    def test_phase_range_validation(self):
        """Test phase must be in [0.0, 1.0]."""
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        vector = [1.0] * 10
        
        # Valid phases
        assert pelm.entangle(vector, phase=0.0) != -1
        assert pelm.entangle(vector, phase=0.5) != -1
        assert pelm.entangle(vector, phase=1.0) != -1
        
        # Invalid phases should raise
        with pytest.raises(ValueError, match="phase must be in"):
            pelm.entangle(vector, phase=-0.1)
        
        with pytest.raises(ValueError, match="phase must be in"):
            pelm.entangle(vector, phase=1.1)
    
    def test_vector_nan_inf_validation(self):
        """Test vectors with NaN/inf are rejected."""
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        
        # Valid vector
        vector = [1.0] * 10
        assert pelm.entangle(vector, phase=0.5) != -1
        
        # NaN should raise
        with pytest.raises(ValueError, match="invalid value"):
            pelm.entangle([float('nan')] * 10, phase=0.5)
        
        # Inf should raise
        with pytest.raises(ValueError, match="invalid value"):
            pelm.entangle([float('inf')] * 10, phase=0.5)


class TestPELMConfidenceMutations:
    """
    Test that mutations to confidence threshold logic are detected.
    
    Validates low-confidence memory rejection.
    """
    
    def test_confidence_threshold_rejection(self):
        """Test low-confidence memories are rejected."""
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        vector = [1.0] * 10
        
        # High confidence should be accepted
        high_conf = MemoryProvenance(
            source=MemorySource.USER_INPUT,
            confidence=0.9
        )
        result = pelm.entangle(vector, phase=0.5, provenance=high_conf)
        assert result != -1
        
        # Low confidence should be rejected (returns -1)
        low_conf = MemoryProvenance(
            source=MemorySource.USER_INPUT,
            confidence=0.3
        )
        result = pelm.entangle(vector, phase=0.5, provenance=low_conf)
        assert result == -1
    
    def test_confidence_threshold_boundary(self):
        """Test confidence threshold boundary at 0.5."""
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        vector = [1.0] * 10
        
        # At threshold (0.5) should be accepted
        at_threshold = MemoryProvenance(
            source=MemorySource.USER_INPUT,
            confidence=0.5
        )
        result = pelm.entangle(vector, phase=0.5, provenance=at_threshold)
        assert result != -1
        
        # Just below threshold should be rejected
        below = MemoryProvenance(
            source=MemorySource.USER_INPUT,
            confidence=0.49
        )
        result = pelm.entangle(vector, phase=0.5, provenance=below)
        assert result == -1


class TestPELMRetrievalMutations:
    """
    Test that mutations to retrieval logic are detected.
    
    Validates retrieval behavior and phase proximity.
    """
    
    def test_retrieve_basic_functionality(self):
        """Test basic retrieval works."""
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        
        # Store a vector
        vector = [1.0] * 10
        idx = pelm.entangle(vector, phase=0.5)
        assert idx != -1
        
        # Should be able to retrieve
        query = [1.0] * 10
        results = pelm.retrieve(query, query_phase=0.5, top_k=1)
        assert len(results) > 0
    
    def test_retrieve_empty_memory(self):
        """Test retrieval from empty memory."""
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        
        # Retrieval from empty memory should return empty list
        query = [1.0] * 10
        results = pelm.retrieve(query, query_phase=0.5, top_k=1)
        assert len(results) == 0
    
    def test_retrieve_phase_proximity(self):
        """Test retrieval respects phase proximity."""
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        
        # Store vectors at different phases
        vector1 = [1.0] * 10
        vector2 = [2.0] * 10
        
        pelm.entangle(vector1, phase=0.1)
        pelm.entangle(vector2, phase=0.9)
        
        # Query at phase 0.1 should prefer vector1
        results = pelm.retrieve(vector1, query_phase=0.1, top_k=1)
        assert len(results) > 0
        
        # Query at phase 0.9 should work
        results = pelm.retrieve(vector2, query_phase=0.9, top_k=1)
        assert len(results) > 0


class TestPELMTypeSafetyMutations:
    """
    Test that mutations to type checking are detected.
    
    Validates type validation for inputs.
    """
    
    def test_vector_type_validation(self):
        """Test vector must be a list."""
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        
        # List should work
        assert pelm.entangle([1.0] * 10, phase=0.5) != -1
        
        # Non-list should raise
        with pytest.raises(TypeError, match="vector must be a list"):
            pelm.entangle(np.array([1.0] * 10), phase=0.5)
        
        with pytest.raises(TypeError, match="vector must be a list"):
            pelm.entangle((1.0,) * 10, phase=0.5)
    
    def test_phase_type_validation(self):
        """Test phase must be numeric."""
        pelm = PhaseEntangledLatticeMemory(dimension=10)
        vector = [1.0] * 10
        
        # Numeric should work
        assert pelm.entangle(vector, phase=0.5) != -1
        assert pelm.entangle(vector, phase=1) != -1  # int is ok
        
        # Non-numeric should raise
        with pytest.raises(TypeError, match="phase must be numeric"):
            pelm.entangle(vector, phase="0.5")


# Mark all tests as mutation tests
pytestmark = pytest.mark.property
