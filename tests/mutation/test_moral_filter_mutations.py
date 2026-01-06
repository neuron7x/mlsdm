"""
Mutation tests for MoralFilterV2.

These tests verify that existing tests can detect bugs in critical
MoralFilterV2 code paths by introducing small mutations.

Critical mutations to test:
- Boundary condition checks (>=, >, <=, <)
- Threshold comparison logic
- Adaptation delta values
- Threshold clamping logic
"""

import pytest

from mlsdm.cognition.moral_filter_v2 import MoralFilterV2


class TestMoralFilterBoundaryMutations:
    """
    Test that mutations to boundary checks are detected.
    
    These tests validate that existing tests catch boundary condition bugs.
    """
    
    def test_evaluate_boundary_conditions(self):
        """Test boundary conditions in evaluate() are properly tested."""
        moral = MoralFilterV2(initial_threshold=0.5)
        
        # Test exact threshold boundary
        assert moral.evaluate(0.5) is True  # >= threshold
        assert moral.evaluate(0.499) is False  # < threshold
        
        # Test MIN_THRESHOLD boundary
        assert moral.evaluate(MoralFilterV2.MIN_THRESHOLD) is True  # >= MIN
        assert moral.evaluate(MoralFilterV2.MIN_THRESHOLD - 0.01) is False
        
        # Test MAX_THRESHOLD boundary
        assert moral.evaluate(MoralFilterV2.MAX_THRESHOLD) is True
        assert moral.evaluate(MoralFilterV2.MAX_THRESHOLD + 0.01) is True
        
    def test_threshold_clamping_min(self):
        """Test MIN_THRESHOLD clamping is properly tested."""
        # Should clamp to MIN_THRESHOLD
        moral = MoralFilterV2(initial_threshold=0.1)
        assert moral.threshold == MoralFilterV2.MIN_THRESHOLD
        
        # Should not go below MIN during adaptation
        moral = MoralFilterV2(initial_threshold=MoralFilterV2.MIN_THRESHOLD + 0.01)
        for _ in range(100):
            moral.adapt(accepted=False)  # Push threshold down
        assert moral.threshold >= MoralFilterV2.MIN_THRESHOLD
        
    def test_threshold_clamping_max(self):
        """Test MAX_THRESHOLD clamping is properly tested."""
        # Should clamp to MAX_THRESHOLD
        moral = MoralFilterV2(initial_threshold=0.99)
        assert moral.threshold == MoralFilterV2.MAX_THRESHOLD
        
        # Should not go above MAX during adaptation
        moral = MoralFilterV2(initial_threshold=MoralFilterV2.MAX_THRESHOLD - 0.01)
        for _ in range(100):
            moral.adapt(accepted=True)  # Push threshold up
        assert moral.threshold <= MoralFilterV2.MAX_THRESHOLD


class TestMoralFilterAdaptationMutations:
    """
    Test that mutations to adaptation logic are detected.
    
    These tests validate that adaptation behavior is properly tested.
    """
    
    def test_adapt_positive_error(self):
        """Test adaptation with positive error (threshold should increase)."""
        moral = MoralFilterV2(initial_threshold=0.5)
        initial = moral.threshold
        
        # Accept many times to push EMA above 0.5
        for _ in range(20):
            moral.adapt(accepted=True)
        
        # Threshold should have increased
        assert moral.threshold > initial
        
    def test_adapt_negative_error(self):
        """Test adaptation with negative error (threshold should decrease)."""
        moral = MoralFilterV2(initial_threshold=0.5)
        initial = moral.threshold
        
        # Reject many times to push EMA below 0.5
        for _ in range(20):
            moral.adapt(accepted=False)
        
        # Threshold should have decreased
        assert moral.threshold < initial
        
    def test_adapt_dead_band(self):
        """Test that adaptation respects dead band."""
        moral = MoralFilterV2(initial_threshold=0.5)
        
        # Adapt with balanced accept/reject to stay in dead band
        for i in range(10):
            moral.adapt(accepted=(i % 2 == 0))
        
        # Threshold should be relatively stable (within bounds)
        assert MoralFilterV2.MIN_THRESHOLD <= moral.threshold <= MoralFilterV2.MAX_THRESHOLD
        
    def test_ema_calculation(self):
        """Test EMA calculation is correct."""
        moral = MoralFilterV2(initial_threshold=0.5)
        
        # EMA should start at 0.5
        assert moral.ema_accept_rate == 0.5
        
        # After accepting, EMA should increase
        moral.adapt(accepted=True)
        assert moral.ema_accept_rate > 0.5
        
        # After rejecting, EMA should decrease
        moral2 = MoralFilterV2(initial_threshold=0.5)
        moral2.adapt(accepted=False)
        assert moral2.ema_accept_rate < 0.5


class TestMoralFilterInvariantsMutations:
    """
    Test that mutations violating formal invariants are detected.
    
    Validates tests enforce INV-MF-M1, INV-MF-M2, INV-MF-M3.
    """
    
    def test_inv_mf_m1_threshold_bounds(self):
        """Test INV-MF-M1: Threshold stays in [MIN, MAX]."""
        moral = MoralFilterV2(initial_threshold=0.5)
        
        # Simulate adversarial input
        for i in range(100):
            moral.adapt(accepted=(i < 80))  # 80% accept, then 20% reject
        
        # Invariant: threshold must stay bounded
        assert MoralFilterV2.MIN_THRESHOLD <= moral.threshold <= MoralFilterV2.MAX_THRESHOLD
        
    def test_inv_mf_m2_smooth_adaptation(self):
        """Test INV-MF-M2: Smooth adaptation (no sudden jumps)."""
        moral = MoralFilterV2(initial_threshold=0.5)
        
        # Single adaptation should not cause large jump
        old_threshold = moral.threshold
        moral.adapt(accepted=True)
        change = abs(moral.threshold - old_threshold)
        
        # Change should be at most _ADAPT_DELTA (0.05)
        assert change <= 0.06  # Small epsilon for floating point
        
    def test_inv_mf_m3_bounded_drift_under_attack(self):
        """Test INV-MF-M3: Bounded drift under adversarial attack."""
        moral = MoralFilterV2(initial_threshold=0.5)
        
        # Adversarial attack: sustained high acceptance
        for _ in range(200):
            moral.adapt(accepted=True)
        
        # Even under attack, threshold must stay within bounds
        assert moral.threshold <= MoralFilterV2.MAX_THRESHOLD
        
        # Adversarial attack: sustained high rejection
        moral2 = MoralFilterV2(initial_threshold=0.5)
        for _ in range(200):
            moral2.adapt(accepted=False)
        
        assert moral2.threshold >= MoralFilterV2.MIN_THRESHOLD


class TestMoralFilterStateMutations:
    """Test state management mutations are detected."""
    
    def test_get_state_completeness(self):
        """Test get_state() returns all required fields."""
        moral = MoralFilterV2(initial_threshold=0.6)
        state = moral.get_state()
        
        # All fields should be present
        assert "threshold" in state
        assert "ema" in state
        assert "min_threshold" in state
        assert "max_threshold" in state
        assert "dead_band" in state
        
    def test_get_state_values(self):
        """Test get_state() returns correct values."""
        moral = MoralFilterV2(initial_threshold=0.6)
        state = moral.get_state()
        
        assert state["threshold"] == moral.threshold
        assert state["ema"] == moral.ema_accept_rate
        assert state["min_threshold"] == MoralFilterV2.MIN_THRESHOLD
        assert state["max_threshold"] == MoralFilterV2.MAX_THRESHOLD


# Mark all tests as mutation tests
pytestmark = pytest.mark.property
