"""
Integration tests for OpenTelemetry tracing.

These tests verify that tracing is properly integrated across the MLSDM pipeline,
using an in-memory exporter to capture and verify spans without external dependencies.

Coverage:
- In-memory exporter for span capture and verification
- LLMWrapper generates expected spans
- NeuroCognitiveEngine pipeline creates proper span hierarchy
- Span attributes are correctly set for observability
"""

import numpy as np
import pytest

from mlsdm.observability.tracing import (
    TracerManager,
    TracingConfig,
    get_tracer_manager,
)


@pytest.fixture(autouse=True)
def reset_tracer_between_tests():
    """Ensure tracer is reset between tests for isolation."""
    TracerManager.reset_instance()
    yield
    TracerManager.reset_instance()


@pytest.fixture
def in_memory_tracer():
    """Create a tracer with in-memory exporter for span verification.
    
    Note: This fixture sets up the global tracer manager with in-memory exporter.
    The autouse fixture ensures cleanup between tests.
    """
    config = TracingConfig(enabled=True, exporter_type="in_memory")
    manager = get_tracer_manager(config)
    manager.initialize()
    return manager


@pytest.fixture
def stub_llm_fn():
    """Create a stub LLM function for testing."""
    def _stub_llm(prompt: str, max_tokens: int) -> str:
        return f"Response to: {prompt[:20]}..."
    return _stub_llm


@pytest.fixture
def stub_embedding_fn():
    """Create a stub embedding function for testing."""
    def _stub_embed(text: str) -> np.ndarray:
        # Create deterministic embedding based on text hash
        np.random.seed(hash(text) % 2**32)
        vec = np.random.randn(384).astype(np.float32)
        return vec / np.linalg.norm(vec)
    return _stub_embed


class TestInMemoryExporter:
    """Tests for in-memory exporter functionality."""

    def test_in_memory_exporter_captures_spans(self, in_memory_tracer):
        """Test that in-memory exporter captures finished spans."""
        # Create a test span
        with in_memory_tracer.start_span("test_span") as span:
            span.set_attribute("test.key", "test_value")

        # Verify span was captured
        spans = in_memory_tracer.get_finished_spans()
        assert len(spans) == 1
        assert spans[0].name == "test_span"
        assert spans[0].attributes["test.key"] == "test_value"

    def test_in_memory_exporter_captures_multiple_spans(self, in_memory_tracer):
        """Test that multiple spans are captured correctly."""
        with in_memory_tracer.start_span("span_1"):
            pass

        with in_memory_tracer.start_span("span_2"):
            pass

        with in_memory_tracer.start_span("span_3"):
            pass

        spans = in_memory_tracer.get_finished_spans()
        assert len(spans) == 3
        span_names = {s.name for s in spans}
        assert span_names == {"span_1", "span_2", "span_3"}

    def test_in_memory_exporter_captures_nested_spans(self, in_memory_tracer):
        """Test that nested spans maintain proper parent-child relationship."""
        with in_memory_tracer.start_span("parent") as parent:
            with in_memory_tracer.start_span("child") as child:
                with in_memory_tracer.start_span("grandchild"):
                    pass

        spans = in_memory_tracer.get_finished_spans()
        assert len(spans) == 3

        # Find spans by name
        span_by_name = {s.name: s for s in spans}

        # Verify child has parent context
        parent_span = span_by_name["parent"]
        child_span = span_by_name["child"]
        grandchild_span = span_by_name["grandchild"]

        # Child's parent should be parent
        assert child_span.parent is not None
        assert child_span.parent.span_id == parent_span.context.span_id

        # Grandchild's parent should be child
        assert grandchild_span.parent is not None
        assert grandchild_span.parent.span_id == child_span.context.span_id

    def test_clear_spans(self, in_memory_tracer):
        """Test that clear_spans removes captured spans."""
        with in_memory_tracer.start_span("span_to_clear"):
            pass

        assert len(in_memory_tracer.get_finished_spans()) == 1

        in_memory_tracer.clear_spans()

        assert len(in_memory_tracer.get_finished_spans()) == 0

    def test_span_attributes_types(self, in_memory_tracer):
        """Test that various attribute types are correctly captured."""
        with in_memory_tracer.start_span("typed_span") as span:
            span.set_attribute("string_attr", "value")
            span.set_attribute("int_attr", 42)
            span.set_attribute("float_attr", 3.14)
            span.set_attribute("bool_attr", True)

        spans = in_memory_tracer.get_finished_spans()
        attrs = dict(spans[0].attributes)

        assert attrs["string_attr"] == "value"
        assert attrs["int_attr"] == 42
        assert attrs["float_attr"] == 3.14
        assert attrs["bool_attr"] is True


class TestLLMWrapperTracing:
    """Tests for LLMWrapper tracing integration."""

    def test_llm_wrapper_generates_spans(
        self, in_memory_tracer, stub_llm_fn, stub_embedding_fn
    ):
        """Test that LLMWrapper.generate() creates expected spans."""
        from mlsdm.core.llm_wrapper import LLMWrapper

        # Clear any spans from initialization
        in_memory_tracer.clear_spans()

        wrapper = LLMWrapper(
            llm_generate_fn=stub_llm_fn,
            embedding_fn=stub_embedding_fn,
            dim=384,
        )

        # Generate a response
        result = wrapper.generate(
            prompt="Hello, how are you?",
            moral_value=0.8,
            max_tokens=128,
        )

        # Get finished spans
        spans = in_memory_tracer.get_finished_spans()

        # Verify at least the main generate span was created
        span_names = {s.name for s in spans}
        assert "llm_wrapper.generate" in span_names

    def test_llm_wrapper_generate_span_has_attributes(
        self, in_memory_tracer, stub_llm_fn, stub_embedding_fn
    ):
        """Test that generate span has expected attributes."""
        from mlsdm.core.llm_wrapper import LLMWrapper

        in_memory_tracer.clear_spans()

        wrapper = LLMWrapper(
            llm_generate_fn=stub_llm_fn,
            embedding_fn=stub_embedding_fn,
            dim=384,
        )

        wrapper.generate(
            prompt="Test prompt",
            moral_value=0.7,
            max_tokens=256,
        )

        spans = in_memory_tracer.get_finished_spans()
        generate_span = next(s for s in spans if s.name == "llm_wrapper.generate")

        # Check expected attributes
        attrs = dict(generate_span.attributes)
        assert "mlsdm.prompt_length" in attrs
        assert attrs["mlsdm.prompt_length"] == len("Test prompt")
        assert "mlsdm.moral_value" in attrs
        assert attrs["mlsdm.moral_value"] == 0.7

    def test_llm_wrapper_creates_child_spans(
        self, in_memory_tracer, stub_llm_fn, stub_embedding_fn
    ):
        """Test that LLMWrapper creates proper child spans for sub-operations."""
        from mlsdm.core.llm_wrapper import LLMWrapper

        in_memory_tracer.clear_spans()

        wrapper = LLMWrapper(
            llm_generate_fn=stub_llm_fn,
            embedding_fn=stub_embedding_fn,
            dim=384,
        )

        wrapper.generate(
            prompt="Generate something",
            moral_value=0.9,
        )

        spans = in_memory_tracer.get_finished_spans()
        span_names = {s.name for s in spans}

        # Verify child spans are created
        expected_spans = {
            "llm_wrapper.generate",
            "llm_wrapper.moral_filter",
            "llm_wrapper.memory_retrieval",
            "llm_wrapper.llm_call",
            "llm_wrapper.memory_update",
        }
        assert expected_spans.issubset(span_names)

    def test_llm_wrapper_moral_rejection_traced(
        self, in_memory_tracer, stub_llm_fn, stub_embedding_fn
    ):
        """Test that moral rejection is properly traced."""
        from mlsdm.core.llm_wrapper import LLMWrapper

        in_memory_tracer.clear_spans()

        wrapper = LLMWrapper(
            llm_generate_fn=stub_llm_fn,
            embedding_fn=stub_embedding_fn,
            dim=384,
        )

        # Low moral value should be rejected
        result = wrapper.generate(
            prompt="Test",
            moral_value=0.1,  # Below default threshold
        )

        # Request should be rejected
        assert result["accepted"] is False

        spans = in_memory_tracer.get_finished_spans()
        generate_span = next(s for s in spans if s.name == "llm_wrapper.generate")

        # Check rejection is recorded
        attrs = dict(generate_span.attributes)
        assert attrs.get("mlsdm.accepted") is False


class TestTracingFallback:
    """Tests for tracing fallback behavior when tracing is disabled."""

    def test_disabled_tracing_does_not_crash(self, stub_llm_fn, stub_embedding_fn):
        """Test that code works when tracing is disabled."""
        from mlsdm.core.llm_wrapper import LLMWrapper

        config = TracingConfig(enabled=False)
        manager = get_tracer_manager(config)
        manager.initialize()

        wrapper = LLMWrapper(
            llm_generate_fn=stub_llm_fn,
            embedding_fn=stub_embedding_fn,
            dim=384,
        )

        # Should work without errors
        result = wrapper.generate(
            prompt="Test prompt",
            moral_value=0.8,
        )

        assert result is not None
        assert "response" in result

    def test_none_exporter_type_does_not_crash(self, stub_llm_fn, stub_embedding_fn):
        """Test that code works with exporter_type='none'."""
        from mlsdm.core.llm_wrapper import LLMWrapper

        config = TracingConfig(enabled=True, exporter_type="none")
        manager = get_tracer_manager(config)
        manager.initialize()

        wrapper = LLMWrapper(
            llm_generate_fn=stub_llm_fn,
            embedding_fn=stub_embedding_fn,
            dim=384,
        )

        result = wrapper.generate(
            prompt="Test prompt",
            moral_value=0.8,
        )

        assert result is not None


class TestTracingWithNeuroCognitiveEngine:
    """Tests for tracing with NeuroCognitiveEngine."""

    def test_engine_creates_pipeline_spans(
        self, in_memory_tracer, stub_llm_fn, stub_embedding_fn
    ):
        """Test that NeuroCognitiveEngine creates full pipeline spans."""
        from mlsdm.engine.neuro_cognitive_engine import (
            NeuroEngineConfig,
            NeuroCognitiveEngine,
        )

        in_memory_tracer.clear_spans()

        config = NeuroEngineConfig(
            dim=384,
            enable_fslgs=False,
            enable_metrics=False,
        )

        engine = NeuroCognitiveEngine(
            llm_generate_fn=stub_llm_fn,
            embedding_fn=stub_embedding_fn,
            config=config,
        )

        result = engine.generate(
            prompt="Generate a response",
            max_tokens=128,
            moral_value=0.8,
        )

        spans = in_memory_tracer.get_finished_spans()
        span_names = {s.name for s in spans}

        # Verify engine-level spans
        assert "engine.generate" in span_names
        assert "engine.moral_precheck" in span_names
        assert "engine.llm_generation" in span_names

    def test_engine_span_attributes(
        self, in_memory_tracer, stub_llm_fn, stub_embedding_fn
    ):
        """Test that engine spans have expected attributes."""
        from mlsdm.engine.neuro_cognitive_engine import (
            NeuroEngineConfig,
            NeuroCognitiveEngine,
        )

        in_memory_tracer.clear_spans()

        config = NeuroEngineConfig(
            dim=384,
            enable_fslgs=False,
        )

        engine = NeuroCognitiveEngine(
            llm_generate_fn=stub_llm_fn,
            embedding_fn=stub_embedding_fn,
            config=config,
        )

        engine.generate(
            prompt="Test prompt for tracing",
            max_tokens=256,
            moral_value=0.75,
        )

        spans = in_memory_tracer.get_finished_spans()
        engine_span = next(s for s in spans if s.name == "engine.generate")

        attrs = dict(engine_span.attributes)
        assert "mlsdm.prompt_length" in attrs
        assert "mlsdm.moral_value" in attrs
        assert attrs["mlsdm.moral_value"] == 0.75


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
