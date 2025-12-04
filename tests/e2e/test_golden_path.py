"""
Golden Path E2E Test for MLSDM.

This test validates the canonical "clone → setup → run → success" path.
It serves as the primary verification that MLSDM is working correctly.

Run with:
    pytest tests/e2e/test_golden_path.py -v
    # or
    make test-golden-path
"""

import pytest


class TestGoldenPath:
    """Golden Path E2E tests - the canonical usage scenario."""

    @pytest.mark.golden_path
    def test_golden_path_create_wrapper(self) -> None:
        """
        Test that create_llm_wrapper() works with defaults.

        This is the first step of the Golden Path.
        """
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()

        assert wrapper is not None
        # Verify initial state
        state = wrapper.get_state()
        assert state["step"] == 0
        assert state["phase"] in ("wake", "sleep")
        assert "qilm_stats" in state
        assert state["qilm_stats"]["capacity"] == 20000

    @pytest.mark.golden_path
    def test_golden_path_generate(self) -> None:
        """
        Test that generate() produces a valid response.

        This is the core step of the Golden Path.
        """
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()

        result = wrapper.generate(
            prompt="Explain machine learning",
            moral_value=0.85,
        )

        # Verify response structure
        assert "response" in result
        assert "accepted" in result
        assert "phase" in result
        assert "step" in result
        assert "moral_threshold" in result

        # Verify acceptance with high moral value
        assert result["accepted"] is True
        assert result["phase"] in ("wake", "sleep")
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0

    @pytest.mark.golden_path
    def test_golden_path_state_updates(self) -> None:
        """
        Test that system state updates after generation.

        Verifies MLSDM's cognitive memory is functioning.
        """
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper()

        # Generate first response
        result1 = wrapper.generate(prompt="Hello", moral_value=0.9)

        state = wrapper.get_state()

        # Verify state updated
        assert state["step"] == 1
        assert state["qilm_stats"]["used"] == 1
        assert state["accepted_count"] == 1

        # Generate second response
        result2 = wrapper.generate(prompt="World", moral_value=0.9)

        state2 = wrapper.get_state()
        assert state2["step"] == 2
        assert state2["qilm_stats"]["used"] == 2
        assert state2["accepted_count"] == 2

    @pytest.mark.golden_path
    def test_golden_path_moral_filtering(self) -> None:
        """
        Test that moral filtering works correctly.

        High moral values should be accepted, low values rejected.
        """
        from mlsdm import create_llm_wrapper

        wrapper = create_llm_wrapper(initial_moral_threshold=0.6)

        # High moral value - should be accepted
        high_result = wrapper.generate(prompt="Good content", moral_value=0.9)
        assert high_result["accepted"] is True

        # Low moral value - should be rejected
        low_result = wrapper.generate(prompt="Bad content", moral_value=0.3)
        assert low_result["accepted"] is False

    @pytest.mark.golden_path
    def test_golden_path_full_demo(self) -> None:
        """
        Test the complete Golden Path demo flow.

        This mirrors what examples/golden_path_demo.py does.
        """
        from mlsdm import create_llm_wrapper

        # 1. Create wrapper with defaults
        wrapper = create_llm_wrapper()
        assert wrapper is not None

        # 2. Generate governed response
        prompt = "Explain what machine learning is in one sentence."
        result = wrapper.generate(prompt=prompt, moral_value=0.85)

        # 3. Verify success
        assert result["accepted"] is True
        assert result["phase"] in ("wake", "sleep")
        assert len(result["response"]) > 0

        # 4. Verify state
        state = wrapper.get_state()
        assert state["step"] == 1
        assert state["qilm_stats"]["used"] == 1
        assert 0.3 <= state["moral_threshold"] <= 0.9

    @pytest.mark.golden_path
    def test_golden_path_neuro_engine(self) -> None:
        """
        Test the NeuroCognitiveEngine path.

        Alternative high-level API for MLSDM.
        """
        from mlsdm import create_neuro_engine

        engine = create_neuro_engine()

        result = engine.generate(
            prompt="What is artificial intelligence?",
            max_tokens=256,
            moral_value=0.85,
        )

        # Verify response
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0

    @pytest.mark.golden_path
    def test_golden_path_sdk_client(self) -> None:
        """
        Test the SDK client path.

        High-level SDK for external integration.
        """
        from mlsdm import NeuroCognitiveClient

        client = NeuroCognitiveClient(backend="local_stub")

        result = client.generate(
            prompt="Explain quantum computing",
            max_tokens=256,
            moral_value=0.8,
        )

        # Verify response
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0
