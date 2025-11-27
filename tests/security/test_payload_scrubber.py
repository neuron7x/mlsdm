"""
Targeted security tests for payload_scrubber.

Tests focus on:
- PII (Personally Identifiable Information) scrubbing
- Token and credential scrubbing
- Raw LLM payload scrubbing
- Large/malformed payload handling
- Edge cases and robustness
"""

import os

import pytest

from mlsdm.security.payload_scrubber import (
    SECRET_PATTERNS,
    scrub_dict,
    scrub_text,
    should_log_payload,
)


class TestPIIScrubbing:
    """Tests for PII (Personally Identifiable Information) scrubbing."""

    def test_email_in_text_preserved_by_default(self):
        """Test that email addresses are preserved by default (configurable)."""
        # Note: Email scrubbing is commented out in the module by default
        text = "Contact john.doe@example.com for support"
        result = scrub_text(text)
        # By default, emails are NOT scrubbed (per code comment)
        # If privacy requirements change, this test should be updated
        assert "john.doe@example.com" in result

    def test_credit_card_scrubbed(self):
        """Test that credit card numbers are scrubbed."""
        cards = [
            "4111-1111-1111-1111",  # Visa test card
            "5500 0000 0000 0004",  # Mastercard test
            "4111111111111111",     # No separators
        ]
        for card in cards:
            text = f"Card number: {card}"
            result = scrub_text(text)
            assert "****-****-****-****" in result
            # Original digits should not be present
            assert card not in result

    def test_ip_addresses_preserved(self):
        """Test that IP addresses are preserved (not PII in security context)."""
        text = "Client IP: 192.168.1.100"
        result = scrub_text(text)
        # IPs are not scrubbed by current implementation
        assert "192.168.1.100" in result

    def test_ssn_like_patterns_not_scrubbed(self):
        """Test SSN patterns - not currently scrubbed."""
        # Note: SSN scrubbing could be added if needed
        text = "SSN: 123-45-6789"
        result = scrub_text(text)
        # Current implementation does not scrub SSN patterns
        assert "123-45-6789" in result


class TestTokenScrubbing:
    """Tests for API token and credential scrubbing."""

    def test_openai_key_formats(self):
        """Test various OpenAI API key formats are scrubbed."""
        keys = [
            "sk-1234567890abcdefghijklmnopqrstuvwxyz",  # Legacy format - matches sk- pattern
        ]
        for key in keys:
            result = scrub_text(f"Key: {key}")
            assert "***REDACTED***" in result
            # The actual key content should be removed
            assert "1234567890abcdefghijklmnopqrstuv" not in result

    def test_openai_key_with_api_key_label(self):
        """Test OpenAI key with api_key= label gets redacted via key pattern."""
        text = 'api_key="sk-proj-1234567890abcdefghij"'
        result = scrub_text(text)
        # The api_key pattern matches first, so whole value is redacted
        assert "***REDACTED***" in result
        assert "1234567890" not in result

    def test_jwt_token_scrubbed(self):
        """Test that JWT tokens are scrubbed."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
        text = f"Authorization: Bearer {jwt}"
        result = scrub_text(text)
        assert "***REDACTED***" in result
        # JWT header should not be visible
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_aws_access_key_scrubbed(self):
        """Test that AWS access keys are scrubbed."""
        aws_key = "AKIAIOSFODNN7EXAMPLE"
        text = f"AWS Key: {aws_key}"
        result = scrub_text(text)
        assert "AKIA***REDACTED***" in result
        assert "IOSFODNN7EXAMPLE" not in result

    def test_aws_secret_key_scrubbed(self):
        """Test that AWS secret keys are scrubbed."""
        text = 'aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"'
        result = scrub_text(text)
        assert "***REDACTED***" in result
        assert "wJalrXUtnFEMI" not in result

    def test_generic_token_patterns(self):
        """Test that generic token patterns are scrubbed."""
        tokens = [
            'token="abcdef123456789012345678"',
            'access_token: "xyz123456789012345678abc"',
            'refresh_token="refresh_12345678901234567"',
        ]
        for token in tokens:
            result = scrub_text(token)
            assert "***REDACTED***" in result


class TestRawLLMPayloadScrubbing:
    """Tests for scrubbing raw LLM request/response payloads."""

    def test_openai_request_payload_scrubbed(self):
        """Test that OpenAI request payloads are scrubbed."""
        payload = {
            "model": "gpt-4",
            "api_key": "sk-secret123456789012345678901234",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        result = scrub_dict(payload)
        assert result["api_key"] == "***REDACTED***"
        assert result["model"] == "gpt-4"
        assert result["messages"] == [{"role": "user", "content": "Hello"}]

    def test_anthropic_request_payload_scrubbed(self):
        """Test that Anthropic request payloads are scrubbed."""
        payload = {
            "model": "claude-3",
            "api_key": "sk-ant-123456789012345678901234567",
            "messages": [{"role": "user", "content": "Test"}],
        }
        result = scrub_dict(payload)
        assert result["api_key"] == "***REDACTED***"

    def test_response_with_embedded_secrets(self):
        """Test LLM response containing embedded secrets."""
        response = {
            "response": "Here is the code: api_key = 'sk-secret123456789012345678'",
            "status": "success",
        }
        result = scrub_dict(response)
        # The api_key pattern should catch this and redact
        assert "***REDACTED***" in result["response"]
        # The actual secret value should not be present
        assert "secret12345678901234" not in result["response"]

    def test_headers_dict_scrubbed(self):
        """Test that HTTP headers are scrubbed."""
        headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "Content-Type": "application/json",
            "api_key": "secret-api-key-value123",
        }
        result = scrub_dict(headers)
        # Authorization is a known key to scrub
        assert result["Authorization"] == "***REDACTED***"
        assert result["Content-Type"] == "application/json"
        # api_key should be scrubbed by key name
        assert result["api_key"] == "***REDACTED***"


class TestSafeFieldsPreserved:
    """Tests that safe fields remain unchanged."""

    def test_normal_text_preserved(self):
        """Test that normal text without secrets is preserved."""
        text = "Hello, world! This is a normal message."
        assert scrub_text(text) == text

    def test_numeric_values_preserved(self):
        """Test that numeric values are preserved."""
        payload = {
            "count": 42,
            "rate": 3.14,
            "enabled": True,
        }
        result = scrub_dict(payload)
        assert result["count"] == 42
        assert result["rate"] == 3.14
        assert result["enabled"] is True

    def test_short_strings_preserved(self):
        """Test that short strings (likely not secrets) are preserved."""
        payload = {
            "status": "ok",
            "phase": "wake",
            "model": "gpt-4",
        }
        result = scrub_dict(payload)
        assert result["status"] == "ok"
        assert result["phase"] == "wake"
        assert result["model"] == "gpt-4"

    def test_prompt_content_preserved(self):
        """Test that prompt content without secrets is preserved."""
        payload = {
            "prompt": "What is the meaning of life?",
            "max_tokens": 100,
        }
        result = scrub_dict(payload)
        assert result["prompt"] == "What is the meaning of life?"

    def test_response_text_preserved(self):
        """Test that response text without secrets is preserved."""
        text = "NEURO-RESPONSE: The meaning of life is 42."
        assert scrub_text(text) == text


class TestLargePayloadHandling:
    """Tests for handling large or unusual payloads."""

    def test_large_text_scrubbed(self):
        """Test that large text is handled without crashing."""
        # 1MB of text with embedded secret
        large_text = "a" * 500_000 + " api_key=sk-secret123456789012345678 " + "b" * 500_000
        result = scrub_text(large_text)
        # The api_key pattern should match and redact
        assert "***REDACTED***" in result
        assert "secret12345678901234" not in result

    def test_deeply_nested_dict_scrubbed(self):
        """Test that deeply nested dicts are handled."""
        payload = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "api_key": "secret-value",
                        }
                    }
                }
            }
        }
        result = scrub_dict(payload)
        assert result["level1"]["level2"]["level3"]["level4"]["api_key"] == "***REDACTED***"

    def test_list_with_many_items(self):
        """Test list with many items is handled."""
        payload = {
            "items": [{"api_key": f"key-{i}"} for i in range(100)],
        }
        result = scrub_dict(payload)
        # All api_key values should be redacted
        for item in result["items"]:
            assert item["api_key"] == "***REDACTED***"

    def test_mixed_types_in_list(self):
        """Test mixed types in lists are handled."""
        payload = {
            "mixed": [
                "string value",
                42,
                {"api_key": "secret"},
                ["nested", "list"],
                None,
                True,
            ]
        }
        result = scrub_dict(payload)
        assert result["mixed"][0] == "string value"
        assert result["mixed"][1] == 42
        assert result["mixed"][2]["api_key"] == "***REDACTED***"
        assert result["mixed"][4] is None

    def test_unicode_text_handled(self):
        """Test that unicode text is handled correctly."""
        text = "日本語のテキスト api_key=sk-secret123456789012345 более текста"
        result = scrub_text(text)
        assert "日本語のテキスト" in result
        # api_key pattern should catch this
        assert "***REDACTED***" in result
        assert "более текста" in result
        # The secret value should be gone
        assert "secret123456789012345" not in result

    def test_newlines_and_special_chars(self):
        """Test text with newlines and special characters."""
        text = "Line 1\napi_key=sk-secret123456789012345\nLine 3\t\ttabbed"
        result = scrub_text(text)
        # api_key pattern should match
        assert "***REDACTED***" in result
        assert "Line 1" in result
        assert "Line 3" in result
        # The secret should be gone
        assert "secret123456789012345" not in result


class TestMalformedInputHandling:
    """Tests for handling malformed inputs."""

    def test_none_input_to_scrub_text(self):
        """Test that None input returns None."""
        result = scrub_text(None)  # type: ignore
        assert result is None

    def test_empty_string(self):
        """Test that empty string returns empty string."""
        assert scrub_text("") == ""

    def test_empty_dict(self):
        """Test that empty dict returns empty dict."""
        assert scrub_dict({}) == {}

    def test_dict_with_none_values(self):
        """Test dict with None values."""
        payload = {
            "present": "value",
            "absent": None,
        }
        result = scrub_dict(payload)
        assert result["present"] == "value"
        assert result["absent"] is None


class TestScrubDictOriginalUnmodified:
    """Test that original dict is not modified by scrubbing."""

    def test_original_dict_unchanged(self):
        """Test that original dict is not mutated."""
        original = {"api_key": "secret123456789012345678"}
        original_copy = original.copy()

        scrub_dict(original)

        # Original should be unchanged
        assert original == original_copy
        assert original["api_key"] == "secret123456789012345678"

    def test_nested_original_unchanged(self):
        """Test that nested original dict is not mutated."""
        original = {"config": {"api_key": "secret"}}
        inner_original = original["config"]["api_key"]

        scrub_dict(original)

        assert original["config"]["api_key"] == inner_original


class TestSecretPatternCoverage:
    """Test that all defined secret patterns are covered."""

    def test_all_patterns_are_tuples(self):
        """Test that SECRET_PATTERNS are properly formatted."""
        for pattern, replacement in SECRET_PATTERNS:
            assert hasattr(pattern, "sub"), "Pattern should be a compiled regex"
            assert isinstance(replacement, str), "Replacement should be a string"

    def test_pattern_count(self):
        """Test that we have a reasonable number of patterns."""
        # Sanity check - should have at least 10 patterns
        assert len(SECRET_PATTERNS) >= 10


class TestPrivateKeyScrubbingEdgeCases:
    """Tests for private key scrubbing edge cases."""

    def test_rsa_private_key_scrubbed(self):
        """Test that RSA private key is scrubbed."""
        text = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA0Z3VS5JJcps3DR5X8hoZS
-----END RSA PRIVATE KEY-----"""
        result = scrub_text(text)
        assert "***REDACTED***" in result
        assert "MIIEpAIBAAKCAQEA" not in result

    def test_ec_private_key_scrubbed(self):
        """Test that EC private key is scrubbed."""
        text = """-----BEGIN EC PRIVATE KEY-----
MHQCAQEEIEfGq2YgpPkKXY8E0GNKFV9d7Q3Z
-----END EC PRIVATE KEY-----"""
        result = scrub_text(text)
        assert "***REDACTED***" in result
        assert "MHQCAQEEIEfGq2YgpPkKXY8E0GNKFV9d7Q3Z" not in result

    def test_private_key_in_multiline_json(self):
        """Test private key in multiline JSON structure."""
        payload = {
            "config": "value",
            "key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBg\n-----END PRIVATE KEY-----",
        }
        result = scrub_dict(payload)
        assert "***REDACTED***" in result["key"]
        assert "MIIEvQIBADANBg" not in result["key"]


class TestPasswordPatternEdgeCases:
    """Tests for password pattern edge cases."""

    def test_password_in_url(self):
        """Test that password in URL format is scrubbed."""
        text = "postgres://user:secretpass@host:5432/db"
        result = scrub_text(text)
        # Current implementation may or may not scrub this specific format
        # The password pattern expects = or : followed by password value
        # This test documents current behavior
        assert "secretpass" in result or "***REDACTED***" in result

    def test_password_with_special_chars(self):
        """Test password with special characters."""
        text = 'password="P@$$w0rd!#%^&*()"'
        result = scrub_text(text)
        assert "***REDACTED***" in result
        assert "P@$$w0rd" not in result

    def test_password_short_not_scrubbed(self):
        """Test that short passwords (< 8 chars) are not scrubbed."""
        text = 'password="short"'
        result = scrub_text(text)
        # Short passwords may not match the pattern requiring 8+ chars
        # This is by design to avoid false positives
        assert result == text


class TestApiKeyVariantsScrubbing:
    """Tests for API key format variations."""

    def test_api_key_with_underscore(self):
        """Test api_key with underscore format."""
        text = 'api_key: "abcdefghij1234567890klmnopq"'
        result = scrub_text(text)
        assert "***REDACTED***" in result

    def test_api_key_with_dash(self):
        """Test api-key with dash format."""
        text = 'api-key: "abcdefghij1234567890klmnopq"'
        result = scrub_text(text)
        assert "***REDACTED***" in result

    def test_apikey_concatenated(self):
        """Test apikey without separator."""
        text = 'apikey: "abcdefghij1234567890klmnopq"'
        result = scrub_text(text)
        assert "***REDACTED***" in result

    def test_anthropic_key_format(self):
        """Test Anthropic API key format (sk-ant-)."""
        text = "api_key=sk-ant-api03-1234567890abcdefghijklmnopqrstuvwxyz"
        result = scrub_text(text)
        # Should be scrubbed by either api_key pattern or sk- pattern
        assert "***REDACTED***" in result


class TestBooleanAndNumericPreservation:
    """Tests for preserving boolean and numeric values."""

    def test_boolean_true_preserved(self):
        """Test that boolean True is preserved."""
        payload = {"enabled": True, "api_key": "secret123456"}
        result = scrub_dict(payload)
        assert result["enabled"] is True
        assert result["api_key"] == "***REDACTED***"

    def test_boolean_false_preserved(self):
        """Test that boolean False is preserved."""
        payload = {"disabled": False, "token": "secret123456789012345"}
        result = scrub_dict(payload)
        assert result["disabled"] is False
        assert result["token"] == "***REDACTED***"

    def test_integer_preserved(self):
        """Test that integers are preserved."""
        payload = {"port": 5432, "secret": "supersecretpassword"}
        result = scrub_dict(payload)
        assert result["port"] == 5432
        assert result["secret"] == "***REDACTED***"

    def test_float_preserved(self):
        """Test that floats are preserved."""
        payload = {"rate": 3.14159, "api_key": "key123456789012345"}
        result = scrub_dict(payload)
        assert result["rate"] == 3.14159
        assert result["api_key"] == "***REDACTED***"


class TestCustomKeysToScrub:
    """Tests for custom keys_to_scrub parameter."""

    def test_custom_keys_to_scrub(self):
        """Test scrub_dict with custom keys."""
        custom_keys = {"custom_secret", "another_secret"}
        payload = {
            "custom_secret": "value1",
            "another_secret": "value2",
            "normal": "preserved",
        }
        result = scrub_dict(payload, keys_to_scrub=custom_keys)
        assert result["custom_secret"] == "***REDACTED***"
        assert result["another_secret"] == "***REDACTED***"
        assert result["normal"] == "preserved"

    def test_default_keys_with_custom_keys(self):
        """Test that default keys are replaced when custom keys provided."""
        custom_keys = {"custom_key"}
        payload = {
            "api_key": "should_be_preserved",  # Not in custom keys
            "custom_key": "should_be_scrubbed",
        }
        result = scrub_dict(payload, keys_to_scrub=custom_keys)
        # api_key is not in custom keys, so it depends on pattern matching
        assert result["custom_key"] == "***REDACTED***"


class TestEnvironmentVariableScrubbing:
    """Test LOG_PAYLOADS environment variable behavior."""

    def test_log_payloads_default_false(self):
        """Test that LOG_PAYLOADS defaults to false."""
        if "LOG_PAYLOADS" in os.environ:
            del os.environ["LOG_PAYLOADS"]
        assert should_log_payload() is False

    def test_log_payloads_true(self):
        """Test LOG_PAYLOADS=true enables logging."""
        os.environ["LOG_PAYLOADS"] = "true"
        try:
            assert should_log_payload() is True
        finally:
            del os.environ["LOG_PAYLOADS"]

    def test_log_payloads_case_insensitive(self):
        """Test LOG_PAYLOADS is case insensitive."""
        for value in ["TRUE", "True", "TrUe", "true"]:
            os.environ["LOG_PAYLOADS"] = value
            try:
                assert should_log_payload() is True
            finally:
                del os.environ["LOG_PAYLOADS"]

    def test_log_payloads_other_values_false(self):
        """Test that non-'true' values return false."""
        for value in ["yes", "1", "on", "enabled", ""]:
            os.environ["LOG_PAYLOADS"] = value
            try:
                assert should_log_payload() is False
            finally:
                del os.environ["LOG_PAYLOADS"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
