"""Tests for adapters/local_stub_adapter.py.

Tests cover:
- build_local_stub_llm_adapter factory function
- Generated responses
- Token limit handling
- Edge cases
"""

from mlsdm.adapters.local_stub_adapter import build_local_stub_llm_adapter


class TestBuildLocalStubLLMAdapter:
    """Tests for build_local_stub_llm_adapter factory."""

    def test_build_returns_callable(self):
        """Test that factory returns a callable function."""
        llm_fn = build_local_stub_llm_adapter()
        assert callable(llm_fn)

    def test_generated_response_format(self):
        """Test that generated response has expected format."""
        llm_fn = build_local_stub_llm_adapter()
        response = llm_fn("Hello world", max_tokens=100)

        assert isinstance(response, str)
        assert response.startswith("NEURO-RESPONSE:")
        assert "Hello world" in response

    def test_prompt_preview_in_response(self):
        """Test that prompt preview is included in response."""
        llm_fn = build_local_stub_llm_adapter()
        prompt = "Test prompt for LLM"
        response = llm_fn(prompt, max_tokens=100)

        assert "Test prompt for LLM" in response

    def test_long_prompt_truncated(self):
        """Test that long prompts are truncated to 50 chars in preview."""
        llm_fn = build_local_stub_llm_adapter()
        long_prompt = "abcdefghij" * 10  # 100 characters with unique chars
        response = llm_fn(long_prompt, max_tokens=100)

        # Should contain first 50 chars
        assert long_prompt[:50] in response
        # Full prompt should not be in response (truncated)
        assert long_prompt not in response

    def test_short_prompt_not_truncated(self):
        """Test that short prompts are not truncated."""
        llm_fn = build_local_stub_llm_adapter()
        short_prompt = "Short"
        response = llm_fn(short_prompt, max_tokens=100)

        assert short_prompt in response

    def test_max_tokens_50_or_less(self):
        """Test response with max_tokens <= 50."""
        llm_fn = build_local_stub_llm_adapter()
        response = llm_fn("Test", max_tokens=50)

        # Should have basic response format
        assert response.startswith("NEURO-RESPONSE:")
        assert "Test" in response
        # Should not have extended message for small max_tokens
        assert "Generated with max_tokens=" not in response

    def test_max_tokens_over_50(self):
        """Test response with max_tokens > 50."""
        llm_fn = build_local_stub_llm_adapter()
        response = llm_fn("Test", max_tokens=100)

        # Should have extended message
        assert "Generated with max_tokens=100" in response
        assert "This is a stub response" in response
        assert "local adapter" in response

    def test_max_tokens_limit_respected(self):
        """Test that response respects max_tokens limit."""
        llm_fn = build_local_stub_llm_adapter()
        response = llm_fn("Test prompt", max_tokens=20)

        # Approximate: 4 chars per token = 80 chars max
        max_chars = 20 * 4
        assert len(response) <= max_chars

    def test_deterministic_responses(self):
        """Test that responses are deterministic for same input."""
        llm_fn = build_local_stub_llm_adapter()

        response1 = llm_fn("Same prompt", max_tokens=100)
        response2 = llm_fn("Same prompt", max_tokens=100)

        # Should be identical
        assert response1 == response2

    def test_different_prompts_different_responses(self):
        """Test that different prompts produce different responses."""
        llm_fn = build_local_stub_llm_adapter()

        response1 = llm_fn("Prompt A", max_tokens=100)
        response2 = llm_fn("Prompt B", max_tokens=100)

        # Should be different (contain different prompts)
        assert response1 != response2
        assert "Prompt A" in response1
        assert "Prompt B" in response2

    def test_empty_prompt(self):
        """Test response with empty prompt."""
        llm_fn = build_local_stub_llm_adapter()
        response = llm_fn("", max_tokens=100)

        assert isinstance(response, str)
        assert response.startswith("NEURO-RESPONSE:")

    def test_very_long_prompt(self):
        """Test response with very long prompt."""
        llm_fn = build_local_stub_llm_adapter()
        very_long_prompt = "x" * 1000
        response = llm_fn(very_long_prompt, max_tokens=100)

        # Should truncate to first 50 chars
        assert very_long_prompt[:50] in response
        assert len(response) < len(very_long_prompt)

    def test_max_tokens_1(self):
        """Test response with minimal max_tokens=1."""
        llm_fn = build_local_stub_llm_adapter()
        response = llm_fn("Test", max_tokens=1)

        # Should respect limit (4 chars max)
        assert len(response) <= 4
        assert isinstance(response, str)

    def test_max_tokens_large(self):
        """Test response with large max_tokens."""
        llm_fn = build_local_stub_llm_adapter()
        response = llm_fn("Test", max_tokens=500)

        # Should include extended message
        assert "Generated with max_tokens=500" in response
        # But still respect overall limit
        max_chars = 500 * 4
        assert len(response) <= max_chars

    def test_unicode_prompt(self):
        """Test response with unicode characters in prompt."""
        llm_fn = build_local_stub_llm_adapter()
        unicode_prompt = "Hello 世界 🌍"
        response = llm_fn(unicode_prompt, max_tokens=100)

        assert isinstance(response, str)
        # Unicode should be preserved in preview
        assert "Hello" in response

    def test_newlines_in_prompt(self):
        """Test response with newlines in prompt."""
        llm_fn = build_local_stub_llm_adapter()
        multiline_prompt = "Line 1\nLine 2\nLine 3"
        response = llm_fn(multiline_prompt, max_tokens=100)

        assert isinstance(response, str)
        assert response.startswith("NEURO-RESPONSE:")

    def test_special_characters_in_prompt(self):
        """Test response with special characters."""
        llm_fn = build_local_stub_llm_adapter()
        special_prompt = "Test: <xml> & 'quotes' \"double\""
        response = llm_fn(special_prompt, max_tokens=100)

        assert isinstance(response, str)
        # Should handle special chars gracefully

    def test_multiple_adapter_instances(self):
        """Test that multiple adapters work independently."""
        llm_fn1 = build_local_stub_llm_adapter()
        llm_fn2 = build_local_stub_llm_adapter()

        response1 = llm_fn1("Test", max_tokens=100)
        response2 = llm_fn2("Test", max_tokens=100)

        # Should produce identical responses (same logic)
        assert response1 == response2

    def test_docstring_example(self):
        """Test the example from docstring."""
        llm_fn = build_local_stub_llm_adapter()
        response = llm_fn("Hello, world!", max_tokens=100)
        assert response.startswith("NEURO-RESPONSE:")

    def test_response_contains_key_elements(self):
        """Test that response contains expected key elements."""
        llm_fn = build_local_stub_llm_adapter()
        response = llm_fn("Test prompt", max_tokens=200)

        # Should contain these elements
        assert "NEURO-RESPONSE:" in response
        assert "Test prompt" in response
        assert "max_tokens=200" in response
        assert "stub response" in response
        assert "NeuroCognitiveEngine pipeline" in response
        assert "without requiring external API calls" in response
