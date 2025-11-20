"""
Tests for circuit breaker pattern in LLM wrapper.

The circuit breaker prevents cascading failures and protects
system stability when the LLM service becomes unavailable.
"""

import numpy as np
import time
import sys
sys.path.insert(0, '.')

from src.core.llm_wrapper import LLMWrapper, CircuitBreakerError


class TestCircuitBreaker:
    """Test circuit breaker failure handling."""
    
    def test_circuit_breaker_opens_on_failures(self):
        """Test that circuit opens after threshold failures."""
        failure_count = 0
        
        def failing_llm(prompt: str, max_tokens: int) -> str:
            nonlocal failure_count
            failure_count += 1
            raise RuntimeError("LLM service unavailable")
        
        def dummy_embed(text: str) -> np.ndarray:
            return np.random.randn(384).astype(np.float32)
        
        wrapper = LLMWrapper(
            llm_generate_fn=failing_llm,
            embedding_fn=dummy_embed,
            dim=384
        )
        
        # Trigger failures until circuit opens
        threshold = wrapper.FAILURE_THRESHOLD
        
        for i in range(threshold):
            result = wrapper.generate(f"test {i}", moral_value=0.8)
            assert not result["accepted"] or "error" in result["note"], \
                f"Expected error on failure {i+1}"
        
        # Circuit should now be OPEN
        from src.core.llm_wrapper import CircuitState
        assert wrapper.circuit_state == CircuitState.OPEN, \
            f"Circuit should be OPEN after {threshold} failures"
        
        print(f"✓ Circuit breaker opened after {threshold} failures")
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery mechanism."""
        failure_mode = True
        
        def conditional_llm(prompt: str, max_tokens: int) -> str:
            if failure_mode:
                raise RuntimeError("LLM service unavailable")
            return "test response"
        
        def dummy_embed(text: str) -> np.ndarray:
            return np.random.randn(384).astype(np.float32)
        
        wrapper = LLMWrapper(
            llm_generate_fn=conditional_llm,
            embedding_fn=dummy_embed,
            dim=384
        )
        
        # Force circuit to open
        threshold = wrapper.FAILURE_THRESHOLD
        for i in range(threshold):
            wrapper.generate(f"test {i}", moral_value=0.8)
        
        from src.core.llm_wrapper import CircuitState
        assert wrapper.circuit_state == CircuitState.OPEN
        
        # Manually advance time to trigger recovery timeout
        wrapper.last_failure_time = time.time() - wrapper.RECOVERY_TIMEOUT - 1
        
        # Fix the LLM
        failure_mode = False
        
        # Next call should attempt recovery (HALF_OPEN)
        result = wrapper.generate("recovery test", moral_value=0.8)
        
        # After successful call, circuit should close
        assert wrapper.circuit_state == CircuitState.CLOSED, \
            "Circuit should be CLOSED after successful recovery"
        
        print("✓ Circuit breaker recovery working")
    
    def test_circuit_breaker_half_open_limit(self):
        """Test that HALF_OPEN state limits test calls."""
        call_count = 0
        
        def counting_llm(prompt: str, max_tokens: int) -> str:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Still failing")
        
        def dummy_embed(text: str) -> np.ndarray:
            return np.random.randn(384).astype(np.float32)
        
        wrapper = LLMWrapper(
            llm_generate_fn=counting_llm,
            embedding_fn=dummy_embed,
            dim=384
        )
        
        # Open circuit
        for i in range(wrapper.FAILURE_THRESHOLD):
            wrapper.generate(f"test {i}", moral_value=0.8)
        
        # Reset call count
        call_count = 0
        
        # Manually trigger recovery timeout
        wrapper.last_failure_time = time.time() - wrapper.RECOVERY_TIMEOUT - 1
        
        # Attempt multiple calls in HALF_OPEN state
        max_half_open = wrapper.HALF_OPEN_MAX_CALLS
        for i in range(max_half_open + 5):
            wrapper.generate(f"recovery {i}", moral_value=0.8)
        
        # Should not exceed max half-open calls
        assert call_count <= max_half_open, \
            f"Made {call_count} calls in HALF_OPEN, expected max {max_half_open}"
        
        print(f"✓ HALF_OPEN state limited to {max_half_open} test calls")
    
    def test_circuit_breaker_prevents_cascading_failures(self):
        """Test that open circuit prevents request flooding."""
        call_count = 0
        
        def counting_failing_llm(prompt: str, max_tokens: int) -> str:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("LLM overloaded")
        
        def dummy_embed(text: str) -> np.ndarray:
            return np.random.randn(384).astype(np.float32)
        
        wrapper = LLMWrapper(
            llm_generate_fn=counting_failing_llm,
            embedding_fn=dummy_embed,
            dim=384
        )
        
        # Open the circuit
        for i in range(wrapper.FAILURE_THRESHOLD):
            wrapper.generate(f"test {i}", moral_value=0.8)
        
        initial_calls = call_count
        
        # Try many more requests with circuit open
        for i in range(100):
            result = wrapper.generate(f"blocked {i}", moral_value=0.8)
            # Should get error response without calling LLM
            assert "error" in result["note"] or not result["accepted"]
        
        # LLM should not have been called after circuit opened
        assert call_count == initial_calls, \
            f"LLM was called {call_count - initial_calls} times with circuit open"
        
        print("✓ Circuit breaker prevents cascading failures")


def run_all_tests():
    """Run all circuit breaker tests."""
    print("\n=== Circuit Breaker Tests ===\n")
    
    test_suite = TestCircuitBreaker()
    test_suite.test_circuit_breaker_opens_on_failures()
    test_suite.test_circuit_breaker_recovery()
    test_suite.test_circuit_breaker_half_open_limit()
    test_suite.test_circuit_breaker_prevents_cascading_failures()
    
    print("\n✅ ALL CIRCUIT BREAKER TESTS PASSED\n")


if __name__ == "__main__":
    run_all_tests()
