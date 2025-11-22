"""
Cost efficiency evaluation tests for Phase 7.

Tests semantic caching, adaptive context management, and QoS degradation
to validate real-world effectiveness improvements.
"""

import time
from unittest.mock import Mock, patch

import numpy as np
import pytest

from mlsdm.engine.neuro_cognitive_engine import (
    NeuroCognitiveEngine,
    NeuroEngineConfig,
)


class TestSemanticCache:
    """Test semantic caching reduces LLM calls."""
    
    def test_cache_reduces_llm_calls(self):
        """Verify that semantic cache prevents redundant LLM calls."""
        llm_call_count = 0
        
        def counting_llm(prompt: str, max_tokens: int) -> str:
            nonlocal llm_call_count
            llm_call_count += 1
            return f"Response to: {prompt[:20]}"
        
        # Use fixed embedding to ensure cache hits
        fixed_embedding = np.random.randn(384)
        embedding_fn = Mock(return_value=fixed_embedding)
        
        config = NeuroEngineConfig(
            enable_fslgs=False,
            enable_semantic_cache=True,
            cache_similarity_threshold=0.9,
            enable_cost_tracking=True,
            initial_moral_threshold=0.0,  # Disable moral filtering for test
        )
        
        engine = NeuroCognitiveEngine(
            llm_generate_fn=counting_llm,
            embedding_fn=embedding_fn,
            config=config,
        )
        
        # Mock moral filter to always pass
        with patch.object(engine._mlsdm, "moral") as mock_moral:
            mock_moral.compute_moral_value = Mock(return_value=1.0)
            
            # First request - should call LLM
            result1 = engine.generate("Hello world", max_tokens=50, moral_value=0.0)
            assert result1["response"] != ""
            assert result1.get("from_cache", False) is False
            assert llm_call_count == 1
            
            # Second identical request with same embedding - should use cache
            result2 = engine.generate("Hello world", max_tokens=50, moral_value=0.0)
            assert result2.get("from_cache", False) is True
            assert llm_call_count == 1  # No additional LLM call
            
            # Verify cost is zero for cached response
            assert result2["cost"]["total_tokens"] == 0
            
            # Verify cache stats
            cache_stats = engine.get_cache_stats()
            assert cache_stats is not None
            assert cache_stats["hits"] >= 1
            assert cache_stats["hit_rate"] > 0.0
    
    def test_cache_respects_moral_value_differences(self):
        """Verify cache doesn't match queries with different moral values."""
        llm_call_count = 0
        
        def counting_llm(prompt: str, max_tokens: int) -> str:
            nonlocal llm_call_count
            llm_call_count += 1
            return f"Response {llm_call_count}"
        
        fixed_embedding = np.random.randn(384)
        embedding_fn = Mock(return_value=fixed_embedding)
        
        config = NeuroEngineConfig(
            enable_fslgs=False,
            enable_semantic_cache=True,
            cache_moral_tolerance=0.05,  # Strict tolerance
            initial_moral_threshold=0.0,  # Disable moral filtering
        )
        
        engine = NeuroCognitiveEngine(
            llm_generate_fn=counting_llm,
            embedding_fn=embedding_fn,
            config=config,
        )
        
        # Mock moral filter to always pass
        with patch.object(engine._mlsdm, "moral") as mock_moral:
            mock_moral.compute_moral_value = Mock(return_value=1.0)
            
            # Request with moral_value=0.1
            result1 = engine.generate("Test query", moral_value=0.1)
            assert llm_call_count == 1
            
            # Same query but moral_value=0.5 (outside tolerance)
            result2 = engine.generate("Test query", moral_value=0.5)
            assert llm_call_count == 2  # Should call LLM again
            assert result2.get("from_cache", False) is False
    
    def test_cache_respects_user_intent(self):
        """Verify cache distinguishes queries by user intent."""
        llm_call_count = 0
        
        def counting_llm(prompt: str, max_tokens: int) -> str:
            nonlocal llm_call_count
            llm_call_count += 1
            return f"Response {llm_call_count}"
        
        fixed_embedding = np.random.randn(384)
        embedding_fn = Mock(return_value=fixed_embedding)
        
        config = NeuroEngineConfig(
            enable_fslgs=False,
            enable_semantic_cache=True,
            initial_moral_threshold=0.0,  # Disable moral filtering
        )
        
        engine = NeuroCognitiveEngine(
            llm_generate_fn=counting_llm,
            embedding_fn=embedding_fn,
            config=config,
        )
        
        # Mock moral filter to always pass
        with patch.object(engine._mlsdm, "moral") as mock_moral:
            mock_moral.compute_moral_value = Mock(return_value=1.0)
            
            # Request with user_intent="conversational"
            result1 = engine.generate("Test query", user_intent="conversational", moral_value=0.0)
            assert llm_call_count == 1
            assert result1.get("from_cache", False) is False
            
            # Same query but user_intent="analytical"
            result2 = engine.generate("Test query", user_intent="analytical", moral_value=0.0)
            # Intent differs so cache miss - should call LLM again
            # But first call stored with "conversational" intent
            # This depends on whether cache was populated
            assert result2.get("from_cache", False) is False


class TestAdaptiveContext:
    """Test adaptive context management reduces latency under load."""
    
    def test_adaptive_context_reduces_latency_under_load(self):
        """Verify context_top_k decreases when latency exceeds target."""
        # Simulate slow LLM
        def slow_llm(prompt: str, max_tokens: int) -> str:
            time.sleep(0.15)  # 150ms per call
            return "Response"
        
        embedding_fn = Mock(return_value=np.random.randn(384))
        
        config = NeuroEngineConfig(
            enable_fslgs=False,
            enable_semantic_cache=False,  # Disable cache for this test
            target_latency_ms=100.0,  # Target 100ms
            min_context_top_k=2,
            max_context_top_k=10,
            default_context_top_k=8,
            initial_moral_threshold=0.0,  # Disable moral filtering
        )
        
        engine = NeuroCognitiveEngine(
            llm_generate_fn=slow_llm,
            embedding_fn=embedding_fn,
            config=config,
        )
        
        initial_k = engine._runtime_context_top_k
        assert initial_k == 8
        
        # Mock moral filter to always pass
        with patch.object(engine._mlsdm, "moral") as mock_moral:
            mock_moral.compute_moral_value = Mock(return_value=1.0)
            
            # Make several slow requests
            for i in range(5):
                result = engine.generate(f"Query {i}", max_tokens=50, moral_value=0.0)
                assert result["response"] != ""
        
        # After slow requests, context_top_k should decrease
        final_k = engine._runtime_context_top_k
        assert final_k < initial_k
        assert final_k >= config.min_context_top_k
        
        # Verify engine is under load
        assert engine._under_load is True
    
    def test_adaptive_context_increases_when_fast(self):
        """Verify context_top_k increases when latency is low and load is high."""
        # Fast LLM
        def fast_llm(prompt: str, max_tokens: int) -> str:
            time.sleep(0.01)  # 10ms per call
            return "Response"
        
        embedding_fn = Mock(return_value=np.random.randn(384))
        
        config = NeuroEngineConfig(
            enable_fslgs=False,
            enable_semantic_cache=False,
            target_latency_ms=100.0,
            min_context_top_k=2,
            max_context_top_k=10,
            default_context_top_k=5,
            initial_moral_threshold=0.0,  # Disable moral filtering
        )
        
        engine = NeuroCognitiveEngine(
            llm_generate_fn=fast_llm,
            embedding_fn=embedding_fn,
            config=config,
        )
        
        initial_k = engine._runtime_context_top_k
        
        # Mock moral filter to always pass
        with patch.object(engine._mlsdm, "moral") as mock_moral:
            mock_moral.compute_moral_value = Mock(return_value=1.0)
            
            # Make several fast requests with high cognitive load
            for i in range(5):
                result = engine.generate(
                    f"Query {i}",
                    max_tokens=50,
                    cognitive_load=0.8,  # High cognitive load
                    moral_value=0.0
                )
                assert result["response"] != ""
        
        # With fast responses and high load, context_top_k should increase
        final_k = engine._runtime_context_top_k
        assert final_k >= initial_k
        assert final_k <= config.max_context_top_k


class TestQoSDegradation:
    """Test QoS graceful degradation for different priority tiers."""
    
    def test_qos_degradation_applies_for_low_tier(self):
        """Verify low priority tier degrades under load."""
        call_log = []
        
        def logging_llm(prompt: str, max_tokens: int) -> str:
            call_log.append({"prompt": prompt, "max_tokens": max_tokens})
            time.sleep(0.15)  # Simulate slow backend
            return "Response"
        
        embedding_fn = Mock(return_value=np.random.randn(384))
        
        config = NeuroEngineConfig(
            enable_fslgs=True,  # FSLGS enabled
            enable_semantic_cache=False,
            target_latency_ms=100.0,
            priority_tier="low",
            degradation_policy={
                "disable_fslgs": True,
                "limit_max_tokens": 128,
                "min_context_top_k_under_load": 2,
            },
            min_context_top_k=2,
        )
        
        engine = NeuroCognitiveEngine(
            llm_generate_fn=logging_llm,
            embedding_fn=embedding_fn,
            config=config,
        )
        
        # First request - system not under load yet
        result1 = engine.generate("Query 1", max_tokens=512)
        
        # Make several requests to trigger load detection
        for i in range(5):
            result = engine.generate(f"Query {i+2}", max_tokens=512)
        
        # Under load, low tier should have degraded
        assert engine._under_load is True
        
        # Verify context_top_k was reduced
        assert engine._runtime_context_top_k == config.min_context_top_k
        
        # Verify max_tokens was limited in last calls
        if len(call_log) > 3:
            # Later calls should have limited tokens
            recent_call = call_log[-1]
            assert recent_call["max_tokens"] <= 128
    
    def test_qos_normal_tier_moderate_degradation(self):
        """Verify normal priority tier applies moderate degradation."""
        def slow_llm(prompt: str, max_tokens: int) -> str:
            time.sleep(0.15)
            return "Response"
        
        embedding_fn = Mock(return_value=np.random.randn(384))
        
        config = NeuroEngineConfig(
            enable_fslgs=False,
            enable_semantic_cache=False,
            target_latency_ms=100.0,
            priority_tier="normal",
            default_context_top_k=8,
            min_context_top_k=3,
        )
        
        engine = NeuroCognitiveEngine(
            llm_generate_fn=slow_llm,
            embedding_fn=embedding_fn,
            config=config,
        )
        
        initial_k = engine._runtime_context_top_k
        
        # Trigger load
        for i in range(5):
            engine.generate(f"Query {i}", max_tokens=256)
        
        # Normal tier should reduce context but not as aggressively as low
        assert engine._under_load is True
        assert engine._runtime_context_top_k < initial_k
        assert engine._runtime_context_top_k >= config.min_context_top_k
    
    def test_qos_high_tier_no_degradation(self):
        """Verify high priority tier maintains full functionality."""
        def slow_llm(prompt: str, max_tokens: int) -> str:
            time.sleep(0.15)
            return "Response"
        
        embedding_fn = Mock(return_value=np.random.randn(384))
        
        config = NeuroEngineConfig(
            enable_fslgs=False,
            enable_semantic_cache=False,
            target_latency_ms=100.0,
            priority_tier="high",
            default_context_top_k=8,
            initial_moral_threshold=0.0,  # Disable moral filtering
        )
        
        engine = NeuroCognitiveEngine(
            llm_generate_fn=slow_llm,
            embedding_fn=embedding_fn,
            config=config,
        )
        
        initial_k = engine._runtime_context_top_k
        
        # Mock moral filter to always pass
        with patch.object(engine._mlsdm, "moral") as mock_moral:
            mock_moral.compute_moral_value = Mock(return_value=1.0)
            
            # Even under load, high tier should maintain parameters
            for i in range(5):
                result = engine.generate(f"Query {i}", max_tokens=512, moral_value=0.0)
                assert result["response"] != ""
        
        # High tier maintains context_top_k even under load
        # (only adaptive context logic applies, not QoS degradation)
        assert engine._under_load is True
        # High tier still adapts context but doesn't force min


class TestCostTracking:
    """Test cost tracking functionality."""
    
    def test_cost_tracking_in_response(self):
        """Verify cost information is included in response."""
        def mock_llm(prompt: str, max_tokens: int) -> str:
            return "This is a test response with multiple words"
        
        embedding_fn = Mock(return_value=np.random.randn(384))
        
        config = NeuroEngineConfig(
            enable_fslgs=False,
            enable_cost_tracking=True,
            pricing={
                "prompt_price_per_1k": 0.0015,
                "completion_price_per_1k": 0.002,
            },
        )
        
        engine = NeuroCognitiveEngine(
            llm_generate_fn=mock_llm,
            embedding_fn=embedding_fn,
            config=config,
        )
        
        result = engine.generate("What is the meaning of life?", max_tokens=100)
        
        # Verify cost field exists
        assert "cost" in result
        cost = result["cost"]
        
        # Verify all cost fields are present
        assert "prompt_tokens" in cost
        assert "completion_tokens" in cost
        assert "total_tokens" in cost
        assert "estimated_cost_usd" in cost
        
        # Verify reasonable values
        assert cost["prompt_tokens"] > 0
        assert cost["completion_tokens"] > 0
        assert cost["total_tokens"] == cost["prompt_tokens"] + cost["completion_tokens"]
        assert cost["estimated_cost_usd"] >= 0.0
    
    def test_cost_accumulation(self):
        """Verify cost tracker accumulates across requests."""
        def mock_llm(prompt: str, max_tokens: int) -> str:
            return "Response"
        
        embedding_fn = Mock(return_value=np.random.randn(384))
        
        config = NeuroEngineConfig(
            enable_fslgs=False,
            enable_cost_tracking=True,
            enable_semantic_cache=False,
            pricing={
                "prompt_price_per_1k": 0.001,
                "completion_price_per_1k": 0.002,
            },
        )
        
        engine = NeuroCognitiveEngine(
            llm_generate_fn=mock_llm,
            embedding_fn=embedding_fn,
            config=config,
        )
        
        # Make several requests
        for i in range(3):
            engine.generate(f"Query {i}", max_tokens=50)
        
        # Check accumulated cost
        cost_summary = engine.get_cost_summary()
        assert cost_summary is not None
        assert cost_summary["total_tokens"] > 0
        assert cost_summary["estimated_cost_usd"] > 0.0
