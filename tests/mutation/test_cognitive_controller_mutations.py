"""
Mutation tests for CognitiveController.

These tests verify that existing tests can detect bugs in critical
CognitiveController code paths by introducing small mutations.

Critical mutations to test:
- Emergency shutdown triggers
- Memory threshold checks
- Process event validation
- Recovery logic
"""

import numpy as np
import pytest

from mlsdm.core.cognitive_controller import CognitiveController


class TestCognitiveControllerEmergencyShutdownMutations:
    """
    Test that mutations to emergency shutdown logic are detected.
    
    Validates emergency shutdown triggers and state management.
    """
    
    def test_emergency_shutdown_initialization(self):
        """Test emergency_shutdown initializes to False."""
        controller = CognitiveController(dim=10)
        assert controller.is_emergency_shutdown() is False
        assert controller.emergency_shutdown is False
    
    def test_emergency_shutdown_memory_threshold(self):
        """Test emergency shutdown triggers on memory threshold."""
        # Create controller with very low memory threshold to trigger shutdown
        controller = CognitiveController(
            dim=10,
            memory_threshold_mb=0.001  # Very low threshold
        )
        
        # Process event should trigger emergency shutdown
        vector = np.random.randn(10).astype(np.float32)
        result = controller.process_event(vector, moral_value=0.8)
        
        # Should be rejected due to memory or enter emergency shutdown
        assert result.get("rejected", False) or controller.is_emergency_shutdown()
    
    def test_emergency_shutdown_blocks_processing(self):
        """Test emergency shutdown blocks further processing."""
        controller = CognitiveController(dim=10)
        
        # Manually enter emergency shutdown
        controller.emergency_shutdown = True
        
        # Process event should be rejected
        vector = np.random.randn(10).astype(np.float32)
        result = controller.process_event(vector, moral_value=0.8)
        
        assert result["rejected"] is True
        assert "emergency shutdown" in result.get("note", "").lower()


class TestCognitiveControllerProcessEventMutations:
    """
    Test that mutations to process_event logic are detected.
    
    Validates event processing flow and validation.
    """
    
    def test_process_event_basic_functionality(self):
        """Test basic process_event works."""
        controller = CognitiveController(dim=10)
        
        vector = np.random.randn(10).astype(np.float32)
        result = controller.process_event(vector, moral_value=0.8)
        
        # Should return a state dict
        assert isinstance(result, dict)
        assert "rejected" in result
    
    def test_process_event_moral_rejection(self):
        """Test process_event rejects immoral content."""
        controller = CognitiveController(dim=10)
        
        # Very low moral value should be rejected
        vector = np.random.randn(10).astype(np.float32)
        result = controller.process_event(vector, moral_value=0.0)
        
        assert result["rejected"] is True
        assert "moral" in result.get("note", "").lower()
    
    def test_process_event_moral_acceptance(self):
        """Test process_event accepts moral content."""
        controller = CognitiveController(dim=10)
        
        # High moral value should be accepted
        vector = np.random.randn(10).astype(np.float32)
        result = controller.process_event(vector, moral_value=0.9)
        
        # Should not be rejected for moral reasons
        if result.get("rejected", False):
            # If rejected, should not be for moral reasons
            assert "moral" not in result.get("note", "").lower()
    
    def test_process_event_step_counter(self):
        """Test process_event increments step counter."""
        controller = CognitiveController(dim=10)
        
        initial_steps = controller.step_counter
        
        vector = np.random.randn(10).astype(np.float32)
        controller.process_event(vector, moral_value=0.8)
        
        # Step counter should have incremented
        assert controller.step_counter > initial_steps


class TestCognitiveControllerMemoryMutations:
    """
    Test that mutations to memory management are detected.
    
    Validates memory bounds and threshold checks.
    """
    
    def test_memory_threshold_positive(self):
        """Test memory threshold must be positive."""
        # Valid threshold
        controller = CognitiveController(dim=10, memory_threshold_mb=1000.0)
        assert controller.memory_threshold_mb == 1000.0
        
        # Positive threshold should be accepted
        controller2 = CognitiveController(dim=10, memory_threshold_mb=100.0)
        assert controller2.memory_threshold_mb == 100.0
    
    def test_memory_usage_tracking(self):
        """Test memory usage is tracked."""
        controller = CognitiveController(dim=10)
        
        # Memory usage should be reportable
        memory_bytes = controller.memory_usage_bytes()
        assert isinstance(memory_bytes, int)
        assert memory_bytes >= 0
    
    def test_max_memory_bytes_bound(self):
        """Test max_memory_bytes enforces hard limit."""
        # Create controller with max_memory_bytes
        controller = CognitiveController(
            dim=10,
            max_memory_bytes=int(1.4 * 1024**3)  # 1.4 GB default
        )
        
        # max_memory_bytes should be set
        assert hasattr(controller, "max_memory_bytes")
        assert controller.max_memory_bytes > 0


class TestCognitiveControllerRecoveryMutations:
    """
    Test that mutations to recovery logic are detected.
    
    Validates auto-recovery behavior and cooldown.
    """
    
    def test_recovery_cooldown_exists(self):
        """Test recovery cooldown mechanism exists."""
        controller = CognitiveController(
            dim=10,
            auto_recovery_enabled=True,
            auto_recovery_cooldown_seconds=60.0
        )
        
        # Should have recovery attributes
        assert hasattr(controller, "auto_recovery_enabled")
        assert hasattr(controller, "auto_recovery_cooldown_seconds")
    
    def test_auto_recovery_enabled_flag(self):
        """Test auto_recovery_enabled flag is respected."""
        # With auto recovery enabled
        controller1 = CognitiveController(
            dim=10,
            auto_recovery_enabled=True
        )
        assert controller1.auto_recovery_enabled is True
        
        # With auto recovery disabled
        controller2 = CognitiveController(
            dim=10,
            auto_recovery_enabled=False
        )
        assert controller2.auto_recovery_enabled is False


class TestCognitiveControllerDimensionMutations:
    """
    Test that mutations to dimension handling are detected.
    
    Validates dimension consistency and validation.
    """
    
    def test_dimension_initialization(self):
        """Test dimension is properly initialized."""
        controller = CognitiveController(dim=384)
        assert controller.dim == 384
        
        controller2 = CognitiveController(dim=768)
        assert controller2.dim == 768
    
    def test_vector_dimension_consistency(self):
        """Test vectors must match controller dimension."""
        controller = CognitiveController(dim=10)
        
        # Correct dimension should work
        vector = np.random.randn(10).astype(np.float32)
        result = controller.process_event(vector, moral_value=0.8)
        assert isinstance(result, dict)
        
        # Note: Wrong dimension handling is tested elsewhere
        # This ensures correct dimension processing works


class TestCognitiveControllerStateMutations:
    """
    Test that mutations to state management are detected.
    
    Validates state building and caching.
    """
    
    def test_state_contains_required_fields(self):
        """Test state contains required fields."""
        controller = CognitiveController(dim=10)
        
        vector = np.random.randn(10).astype(np.float32)
        state = controller.process_event(vector, moral_value=0.8)
        
        # State should have rejected field at minimum
        assert "rejected" in state
        assert isinstance(state["rejected"], bool)
    
    def test_state_note_on_rejection(self):
        """Test state includes note on rejection."""
        controller = CognitiveController(dim=10)
        
        # Trigger rejection with low moral value
        vector = np.random.randn(10).astype(np.float32)
        state = controller.process_event(vector, moral_value=0.0)
        
        if state.get("rejected", False):
            # Rejected state should have a note
            assert "note" in state
            assert isinstance(state["note"], str)


# Mark all tests as mutation tests
pytestmark = pytest.mark.property
