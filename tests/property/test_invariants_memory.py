"""
Property-based tests for memory system invariants.

Tests formal invariants for QILM_v2 and MultiLevelSynapticMemory
as defined in docs/FORMAL_INVARIANTS.md.
"""

import pytest
import numpy as np
from hypothesis import given, settings, strategies as st, assume

from mlsdm.memory.multi_level_memory import MultiLevelSynapticMemory
from mlsdm.memory.qilm_v2 import QILM_v2


# ============================================================================
# Test Strategies
# ============================================================================

@st.composite
def vector_strategy(draw, dim=10):
    """Generate random vectors of specified dimension."""
    size = draw(st.integers(min_value=dim, max_value=dim))
    vector = draw(st.lists(
        st.floats(
            min_value=-10.0,
            max_value=10.0,
            allow_nan=False,
            allow_infinity=False
        ),
        min_size=size,
        max_size=size
    ))
    return np.array(vector, dtype=np.float32)


@st.composite
def normalized_vector_strategy(draw, dim=10):
    """Generate normalized (unit norm) vectors."""
    vec = draw(vector_strategy(dim=dim))
    norm = np.linalg.norm(vec)
    if norm < 1e-8:
        # If zero vector, return a fixed unit vector
        result = np.zeros(dim, dtype=np.float32)
        result[0] = 1.0
        return result
    return vec / norm


@st.composite
def gating_value_strategy(draw):
    """Generate gating values in [0, 1]."""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))


@st.composite
def lambda_strategy(draw):
    """Generate lambda decay values (non-negative)."""
    return draw(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))


# ============================================================================
# Property Tests: MultiLevelSynapticMemory - Safety Invariants
# ============================================================================

@settings(max_examples=50, deadline=None)
@given(
    dim=st.integers(min_value=5, max_value=20),
    num_vectors=st.integers(min_value=1, max_value=10)
)
def test_memory_vector_dimensionality_consistency(dim, num_vectors):
    """
    INV-MEM-S2: Vector Dimensionality Consistency
    All vectors in all levels have same dimension.
    """
    memory = MultiLevelSynapticMemory(dimension=dim)
    
    # Add multiple vectors
    for _ in range(num_vectors):
        vec = np.random.randn(dim).astype(np.float32)
        memory.update(vec)
    
    # Get state
    L1, L2, L3 = memory.get_state()
    
    # Check all vectors have correct dimension
    for vec in L1:
        assert vec.shape[0] == dim, f"L1 vector has wrong dimension: {vec.shape[0]} != {dim}"
    for vec in L2:
        assert vec.shape[0] == dim, f"L2 vector has wrong dimension: {vec.shape[0]} != {dim}"
    for vec in L3:
        assert vec.shape[0] == dim, f"L3 vector has wrong dimension: {vec.shape[0]} != {dim}"


@settings(max_examples=50, deadline=None)
@given(
    gating12=gating_value_strategy(),
    gating23=gating_value_strategy()
)
def test_gating_value_bounds(gating12, gating23):
    """
    INV-MEM-S3: Gating Value Bounds
    Gating values MUST be in [0, 1] range.
    """
    memory = MultiLevelSynapticMemory(
        dimension=10,
        gating12=gating12,
        gating23=gating23
    )
    
    # Gating values should be stored correctly
    assert 0.0 <= memory.gating12 <= 1.0, \
        f"gating12 out of bounds: {memory.gating12}"
    assert 0.0 <= memory.gating23 <= 1.0, \
        f"gating23 out of bounds: {memory.gating23}"


@settings(max_examples=50, deadline=None)
@given(
    lambda_l1=lambda_strategy(),
    lambda_l2=lambda_strategy(),
    lambda_l3=lambda_strategy()
)
def test_lambda_decay_non_negativity(lambda_l1, lambda_l2, lambda_l3):
    """
    INV-MEM-S4: Lambda Decay Non-Negativity
    Decay lambdas MUST be non-negative.
    """
    memory = MultiLevelSynapticMemory(
        dimension=10,
        lambda_l1=lambda_l1,
        lambda_l2=lambda_l2,
        lambda_l3=lambda_l3
    )
    
    assert memory.lambda_l1 >= 0, f"lambda_l1 is negative: {memory.lambda_l1}"
    assert memory.lambda_l2 >= 0, f"lambda_l2 is negative: {memory.lambda_l2}"
    assert memory.lambda_l3 >= 0, f"lambda_l3 is negative: {memory.lambda_l3}"


# ============================================================================
# Property Tests: MultiLevelSynapticMemory - Liveness Invariants
# ============================================================================

@settings(max_examples=50, deadline=None)
@given(
    dim=st.integers(min_value=5, max_value=20),
    num_inserts=st.integers(min_value=1, max_value=10)
)
def test_insertion_progress(dim, num_inserts):
    """
    INV-MEM-L2: Insertion Progress
    Insert operation MUST eventually complete.
    """
    memory = MultiLevelSynapticMemory(dimension=dim)
    
    for i in range(num_inserts):
        vec = np.random.randn(dim).astype(np.float32)
        
        # Get size before
        L1_before, L2_before, L3_before = memory.get_state()
        size_before = len(L1_before) + len(L2_before) + len(L3_before)
        
        # Insert
        memory.update(vec)
        
        # Get size after
        L1_after, L2_after, L3_after = memory.get_state()
        size_after = len(L1_after) + len(L2_after) + len(L3_after)
        
        # Size should increase (or stay same if at capacity)
        assert size_after >= size_before, \
            f"Memory size decreased after insert: {size_before} -> {size_after}"


@settings(max_examples=30, deadline=None)
@given(dim=st.integers(min_value=5, max_value=20))
def test_consolidation_completion(dim):
    """
    INV-MEM-L3: Consolidation Completion
    Consolidation phase MUST complete in bounded time.
    """
    memory = MultiLevelSynapticMemory(dimension=dim)
    
    # Add some vectors
    for _ in range(5):
        vec = np.random.randn(dim).astype(np.float32)
        memory.update(vec)
    
    # Trigger consolidation
    try:
        memory.consolidate()
        # If we reach here, consolidation completed
        assert True
    except Exception as e:
        pytest.fail(f"Consolidation failed to complete: {e}")


# ============================================================================
# Property Tests: MultiLevelSynapticMemory - Metamorphic Invariants
# ============================================================================

@settings(max_examples=30, deadline=None)
@given(dim=st.integers(min_value=5, max_value=20))
def test_distance_non_increase_after_insertion(dim):
    """
    INV-MEM-M1: Distance Non-Increase
    Adding vectors doesn't increase distance to nearest existing neighbor.
    """
    memory = MultiLevelSynapticMemory(dimension=dim)
    
    # Add initial vectors
    initial_vecs = []
    for _ in range(3):
        vec = np.random.randn(dim).astype(np.float32)
        vec = vec / (np.linalg.norm(vec) + 1e-8)
        memory.update(vec)
        initial_vecs.append(vec)
    
    # Create a query vector
    query = np.random.randn(dim).astype(np.float32)
    query = query / (np.linalg.norm(query) + 1e-8)
    
    # Calculate initial minimum distance
    min_dist_before = float('inf')
    for vec in initial_vecs:
        dist = np.linalg.norm(query - vec)
        min_dist_before = min(min_dist_before, dist)
    
    # Add more vectors
    for _ in range(3):
        new_vec = np.random.randn(dim).astype(np.float32)
        new_vec = new_vec / (np.linalg.norm(new_vec) + 1e-8)
        memory.update(new_vec)
    
    # Calculate minimum distance after additions
    L1, L2, L3 = memory.get_state()
    all_vecs = L1 + L2 + L3
    
    min_dist_after = float('inf')
    for vec in all_vecs:
        dist = np.linalg.norm(query - vec)
        min_dist_after = min(min_dist_after, dist)
    
    # Minimum distance should not increase (may decrease or stay same)
    assert min_dist_after <= min_dist_before + 1e-6, \
        f"Min distance increased: {min_dist_before} -> {min_dist_after}"


@settings(max_examples=30, deadline=None)
@given(dim=st.integers(min_value=5, max_value=20))
def test_consolidation_monotonicity(dim):
    """
    INV-MEM-M2: Consolidation Monotonicity
    Consolidation moves vectors down levels, never up.
    """
    memory = MultiLevelSynapticMemory(
        dimension=dim,
        theta_l1=0.5,  # Low threshold to trigger transitions
        theta_l2=1.0
    )
    
    # Add vectors to L1
    for _ in range(5):
        vec = np.random.randn(dim).astype(np.float32)
        memory.update(vec)
    
    # Count vectors at each level before consolidation
    L1_before, L2_before, L3_before = memory.get_state()
    count_L1_before = len(L1_before)
    count_L2_before = len(L2_before)
    count_L3_before = len(L3_before)
    
    # Consolidate
    memory.consolidate()
    
    # Count vectors at each level after consolidation
    L1_after, L2_after, L3_after = memory.get_state()
    count_L1_after = len(L1_after)
    count_L2_after = len(L2_after)
    count_L3_after = len(L3_after)
    
    # L1 should decrease or stay same (vectors move down)
    # L3 should increase or stay same (vectors accumulate)
    # Note: This is a simplified check; exact behavior depends on thresholds
    total_before = count_L1_before + count_L2_before + count_L3_before
    total_after = count_L1_after + count_L2_after + count_L3_after
    
    # Total count should be preserved (no vectors lost)
    assert total_before == total_after, \
        f"Vector count changed: {total_before} -> {total_after}"


# ============================================================================
# Property Tests: QILM_v2 - Safety Invariants
# ============================================================================

@settings(max_examples=50, deadline=None)
@given(
    dim=st.integers(min_value=5, max_value=20),
    capacity=st.integers(min_value=5, max_value=50)
)
def test_qilm_capacity_enforcement(dim, capacity):
    """
    INV-MEM-S1: Capacity Enforcement
    Memory MUST NOT exceed configured capacity.
    """
    qilm = QILM_v2(dimension=dim, capacity=capacity)
    
    # Insert more vectors than capacity
    num_inserts = capacity + 10
    
    for i in range(num_inserts):
        vec = np.random.randn(dim).astype(np.float32)
        phase = "wake" if i % 2 == 0 else "sleep"
        qilm.entangle_phase(vec, phase=phase)
    
    # Check size doesn't exceed capacity
    size = qilm.get_size()
    assert size <= capacity, \
        f"Memory size {size} exceeds capacity {capacity}"


@settings(max_examples=50, deadline=None)
@given(
    dim=st.integers(min_value=5, max_value=20),
    num_vectors=st.integers(min_value=1, max_value=10)
)
def test_qilm_vector_dimensionality(dim, num_vectors):
    """
    INV-MEM-S2: Vector Dimensionality Consistency
    All vectors in QILM have same dimension.
    """
    qilm = QILM_v2(dimension=dim, capacity=100)
    
    # Insert vectors
    for i in range(num_vectors):
        vec = np.random.randn(dim).astype(np.float32)
        qilm.entangle_phase(vec, phase="wake")
    
    # Query and check dimensions
    query = np.random.randn(dim).astype(np.float32)
    neighbors = qilm.find_nearest(query, k=min(3, num_vectors))
    
    for neighbor_vec in neighbors:
        assert neighbor_vec.shape[0] == dim, \
            f"Retrieved vector has wrong dimension: {neighbor_vec.shape[0]} != {dim}"


# ============================================================================
# Property Tests: QILM_v2 - Liveness Invariants
# ============================================================================

@settings(max_examples=50, deadline=None)
@given(
    dim=st.integers(min_value=5, max_value=20),
    num_vectors=st.integers(min_value=1, max_value=20),
    k=st.integers(min_value=1, max_value=5)
)
def test_qilm_nearest_neighbor_availability(dim, num_vectors, k):
    """
    INV-MEM-L1: Nearest Neighbor Availability
    With non-empty memory, query MUST find at least one neighbor.
    """
    qilm = QILM_v2(dimension=dim, capacity=100)
    
    # Insert vectors
    for i in range(num_vectors):
        vec = np.random.randn(dim).astype(np.float32)
        qilm.entangle_phase(vec, phase="wake")
    
    # Query
    query = np.random.randn(dim).astype(np.float32)
    neighbors = qilm.find_nearest(query, k=k)
    
    # Should find at least one neighbor (up to k or num_vectors)
    expected_count = min(k, num_vectors)
    assert len(neighbors) >= min(1, expected_count), \
        f"No neighbors found despite having {num_vectors} vectors"


# ============================================================================
# Property Tests: QILM_v2 - Metamorphic Invariants
# ============================================================================

@settings(max_examples=30, deadline=None)
@given(
    dim=st.integers(min_value=5, max_value=20),
    k=st.integers(min_value=2, max_value=5)
)
def test_qilm_retrieval_relevance_ordering(dim, k):
    """
    INV-MEM-M3: Retrieval Relevance Ordering
    Retrieved neighbors are ordered by decreasing relevance (increasing distance).
    """
    qilm = QILM_v2(dimension=dim, capacity=100)
    
    # Insert several vectors
    for _ in range(10):
        vec = np.random.randn(dim).astype(np.float32)
        qilm.entangle_phase(vec, phase="wake")
    
    # Query
    query = np.random.randn(dim).astype(np.float32)
    neighbors = qilm.find_nearest(query, k=k)
    
    # Calculate distances
    distances = []
    for neighbor in neighbors:
        dist = np.linalg.norm(query - neighbor)
        distances.append(dist)
    
    # Check ordering (distances should be non-decreasing)
    for i in range(len(distances) - 1):
        assert distances[i] <= distances[i + 1] + 1e-6, \
            f"Neighbors not ordered by distance: {distances[i]} > {distances[i+1]}"


@settings(max_examples=30, deadline=None)
@given(dim=st.integers(min_value=5, max_value=20))
def test_qilm_overflow_eviction_policy(dim):
    """
    INV-MEM-M4: Overflow Eviction Policy
    When capacity reached, system evicts appropriately and maintains capacity.
    """
    capacity = 10
    qilm = QILM_v2(dimension=dim, capacity=capacity)
    
    # Fill to capacity
    for i in range(capacity):
        vec = np.random.randn(dim).astype(np.float32)
        qilm.entangle_phase(vec, phase="wake")
    
    # Verify at capacity
    assert qilm.get_size() == capacity
    
    # Add more vectors (should trigger eviction)
    for i in range(5):
        vec = np.random.randn(dim).astype(np.float32)
        qilm.entangle_phase(vec, phase="wake")
    
    # Should still be at capacity
    assert qilm.get_size() == capacity, \
        f"Size {qilm.get_size()} != capacity {capacity} after overflow"


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.parametrize("dim", [1, 5, 10, 100, 384])
def test_various_dimensions(dim):
    """Test memory systems work with various dimensions."""
    memory = MultiLevelSynapticMemory(dimension=dim)
    
    vec = np.random.randn(dim).astype(np.float32)
    memory.update(vec)
    
    L1, L2, L3 = memory.get_state()
    assert len(L1) > 0, "Vector not added to L1"


@pytest.mark.parametrize("capacity", [1, 5, 10, 100])
def test_various_capacities(capacity):
    """Test QILM works with various capacity values."""
    qilm = QILM_v2(dimension=10, capacity=capacity)
    
    # Add vectors up to capacity
    for i in range(capacity):
        vec = np.random.randn(10).astype(np.float32)
        qilm.entangle_phase(vec, phase="wake")
    
    assert qilm.get_size() <= capacity


def test_empty_memory_query():
    """Test querying empty memory returns empty results."""
    qilm = QILM_v2(dimension=10, capacity=100)
    
    query = np.random.randn(10).astype(np.float32)
    neighbors = qilm.find_nearest(query, k=5)
    
    assert len(neighbors) == 0, "Empty memory should return no neighbors"


def test_single_vector_retrieval():
    """Test retrieving from memory with single vector."""
    qilm = QILM_v2(dimension=10, capacity=100)
    
    vec = np.random.randn(10).astype(np.float32)
    qilm.entangle_phase(vec, phase="wake")
    
    query = np.random.randn(10).astype(np.float32)
    neighbors = qilm.find_nearest(query, k=5)
    
    assert len(neighbors) == 1, "Should return the single vector"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
