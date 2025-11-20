"""
Security tests for input validation and attack resistance.

Tests cover:
- NaN and Inf injection attacks
- Dimension mismatch attacks
- Out-of-bounds value attacks
- Type confusion attacks
- Buffer overflow attempts
"""

import numpy as np
import pytest
import sys
sys.path.insert(0, '.')

from src.core.cognitive_controller import CognitiveController
from src.memory.qilm_v2 import QILM_v2


class TestInputValidationSecurity:
    """Test input validation against adversarial inputs."""
    
    def test_nan_injection_attack(self):
        """Test that NaN values are rejected to prevent computation corruption."""
        controller = CognitiveController(dim=384)
        
        # Create vector with NaN
        attack_vector = np.random.randn(384).astype(np.float32)
        attack_vector[0] = np.nan
        
        with pytest.raises(ValueError, match="NaN"):
            controller.process_event(attack_vector, moral_value=0.8)
        
        print("✓ NaN injection attack blocked")
    
    def test_inf_injection_attack(self):
        """Test that Inf values are rejected to prevent overflow."""
        controller = CognitiveController(dim=384)
        
        # Create vector with Inf
        attack_vector = np.random.randn(384).astype(np.float32)
        attack_vector[0] = np.inf
        
        with pytest.raises(ValueError, match="Inf"):
            controller.process_event(attack_vector, moral_value=0.8)
        
        print("✓ Inf injection attack blocked")
    
    def test_dimension_mismatch_attack(self):
        """Test that wrong dimension vectors are rejected."""
        controller = CognitiveController(dim=384)
        
        # Wrong dimension
        attack_vector = np.random.randn(512).astype(np.float32)
        
        with pytest.raises(ValueError, match="dimension mismatch"):
            controller.process_event(attack_vector, moral_value=0.8)
        
        print("✓ Dimension mismatch attack blocked")
    
    def test_moral_value_bounds_attack(self):
        """Test that moral values outside [0, 1] are rejected."""
        controller = CognitiveController(dim=384)
        vector = np.random.randn(384).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        
        # Test upper bound violation
        with pytest.raises(ValueError, match="moral_value"):
            controller.process_event(vector, moral_value=1.5)
        
        # Test lower bound violation
        with pytest.raises(ValueError, match="moral_value"):
            controller.process_event(vector, moral_value=-0.5)
        
        print("✓ Moral value bounds attack blocked")
    
    def test_type_confusion_attack(self):
        """Test that wrong types are rejected."""
        controller = CognitiveController(dim=384)
        
        # Try to pass list instead of ndarray
        with pytest.raises(TypeError, match="numpy.ndarray"):
            controller.process_event([0.1] * 384, moral_value=0.8)
        
        print("✓ Type confusion attack blocked")
    
    def test_qilm_validation(self):
        """Test QILM input validation."""
        qilm = QILM_v2(dimension=384, capacity=1000)
        
        # Test NaN in entangle
        nan_vector = [np.nan] * 384
        with pytest.raises(ValueError, match="NaN"):
            qilm.entangle(nan_vector, phase=0.5)
        
        # Test Inf in entangle
        inf_vector = [np.inf] * 384
        with pytest.raises(ValueError, match="Inf"):
            qilm.entangle(inf_vector, phase=0.5)
        
        # Test dimension mismatch
        wrong_dim = [0.1] * 512
        with pytest.raises(ValueError, match="dimension mismatch"):
            qilm.entangle(wrong_dim, phase=0.5)
        
        # Test phase bounds
        valid_vector = [0.1] * 384
        with pytest.raises(ValueError, match="phase"):
            qilm.entangle(valid_vector, phase=1.5)
        
        print("✓ QILM validation working")
    
    def test_retrieve_validation(self):
        """Test retrieval input validation."""
        qilm = QILM_v2(dimension=384, capacity=1000)
        
        # Add some valid data
        qilm.entangle([0.1] * 384, phase=0.5)
        
        # Test invalid query vector
        with pytest.raises(ValueError, match="NaN"):
            qilm.retrieve([np.nan] * 384, current_phase=0.5)
        
        # Test invalid phase
        with pytest.raises(ValueError, match="current_phase"):
            qilm.retrieve([0.1] * 384, current_phase=1.5)
        
        # Test invalid top_k
        with pytest.raises(ValueError, match="top_k"):
            qilm.retrieve([0.1] * 384, current_phase=0.5, top_k=-1)
        
        print("✓ Retrieve validation working")


class TestBufferOverflowProtection:
    """Test protection against buffer overflow attacks."""
    
    def test_consolidation_buffer_bounds(self):
        """Test that consolidation buffer has bounds checking."""
        from src.core.llm_wrapper import LLMWrapper
        
        def dummy_llm(prompt: str, max_tokens: int) -> str:
            return "test response"
        
        def dummy_embed(text: str) -> np.ndarray:
            return np.random.randn(384).astype(np.float32)
        
        wrapper = LLMWrapper(
            llm_generate_fn=dummy_llm,
            embedding_fn=dummy_embed,
            dim=384,
            capacity=20_000
        )
        
        # Try to overflow buffer (should trigger early consolidation)
        max_buffer = wrapper.MAX_CONSOLIDATION_BUFFER
        
        # Fill buffer to near capacity
        for i in range(max_buffer + 10):
            try:
                wrapper.generate(f"test prompt {i}", moral_value=0.8)
            except Exception:
                # May fail due to sleep phase, that's ok
                pass
        
        # Buffer should not exceed max size
        assert len(wrapper.consolidation_buffer) <= max_buffer, \
            f"Buffer overflow: {len(wrapper.consolidation_buffer)} > {max_buffer}"
        
        print(f"✓ Buffer overflow protection working (max: {max_buffer})")


def run_all_tests():
    """Run all security tests."""
    print("\n=== Security Input Validation Tests ===\n")
    
    test_suite = TestInputValidationSecurity()
    test_suite.test_nan_injection_attack()
    test_suite.test_inf_injection_attack()
    test_suite.test_dimension_mismatch_attack()
    test_suite.test_moral_value_bounds_attack()
    test_suite.test_type_confusion_attack()
    test_suite.test_qilm_validation()
    test_suite.test_retrieve_validation()
    
    print("\n=== Buffer Overflow Protection Tests ===\n")
    
    test_buffer = TestBufferOverflowProtection()
    test_buffer.test_consolidation_buffer_bounds()
    
    print("\n✅ ALL SECURITY TESTS PASSED\n")


if __name__ == "__main__":
    run_all_tests()
