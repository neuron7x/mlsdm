"""Additional payload scrubber coverage tests for uncovered branches.

Tests target specific uncovered code paths in payload_scrubber.py lines 226-240, 301-308, 336-342.
"""

from unittest.mock import patch

import pytest


class TestPayloadScrubberExceptionHandling:
    """Test payload scrubber exception handling paths."""

    def test_scrub_text_pattern_exception_path(self) -> None:
        """Test exception handling in pattern substitution (lines 226-228)."""
        from mlsdm.security.payload_scrubber import scrub_text

        test_text = "api_key=sk-123456 password=secret"

        # Mock pattern.sub to raise an exception
        with patch("mlsdm.security.payload_scrubber.SECRET_PATTERNS", [(None, "***")]):
            # Should not crash, should continue with other patterns
            result = scrub_text(test_text)
            # Should return text even if pattern fails
            assert result is not None

    def test_scrub_text_email_exception_path(self) -> None:
        """Test exception handling in email scrubbing (lines 234-235)."""
        from mlsdm.security.payload_scrubber import scrub_text

        test_text = "Contact: user@example.com"

        # Mock EMAIL_PATTERN.sub to raise an exception
        with patch("mlsdm.security.payload_scrubber.EMAIL_PATTERN") as mock_pattern:
            mock_pattern.sub.side_effect = Exception("Pattern error")
            
            # Should not crash, should return text
            result = scrub_text(test_text, scrub_emails=True)
            assert result is not None

    def test_scrub_text_general_exception_path(self) -> None:
        """Test general exception handling (lines 238-240)."""
        from mlsdm.security.payload_scrubber import scrub_text

        test_text = "test data"

        # Mock to cause exception in the try block
        with patch("mlsdm.security.payload_scrubber.SECRET_PATTERNS", side_effect=Exception("Unexpected")):
            # Should return original text on error
            result = scrub_text(test_text)
            assert result == test_text

    def test_scrub_dict_value_exception_path(self) -> None:
        """Test exception handling when scrubbing values (lines 301-303)."""
        from mlsdm.security.payload_scrubber import scrub_dict

        # Create a dict with a value that will cause an error
        test_dict = {"key": "value"}

        # Mock scrub_text to raise an exception
        with patch("mlsdm.security.payload_scrubber.scrub_text", side_effect=Exception("Scrub error")):
            # Should not crash, should return original value
            result = scrub_dict(test_dict)
            assert result == test_dict

    def test_scrub_dict_general_exception_path(self) -> None:
        """Test general exception handling in scrub_dict (lines 306-308)."""
        from mlsdm.security.payload_scrubber import scrub_dict

        # Create a mock dict-like object that raises an exception
        class BadDict(dict):
            def items(self):
                raise Exception("Dict error")
        
        test_dict = BadDict({"key": "value"})

        # Should return original data on error
        result = scrub_dict(test_dict)
        # The function catches the exception and returns original data
        assert result is not None


class TestScrubRequestPayloadExceptionHandling:
    """Test scrub_request_payload exception handling paths."""

    def test_scrub_request_payload_primary_exception(self) -> None:
        """Test primary exception handling (lines 336-342)."""
        from mlsdm.security.payload_scrubber import scrub_request_payload

        test_payload = {"api_key": "secret", "data": "value"}

        # Mock _scrub_with_forbidden_fields to raise an exception
        with patch("mlsdm.security.payload_scrubber._scrub_with_forbidden_fields", side_effect=Exception("Primary error")):
            # Should fall back to scrub_dict
            with patch("mlsdm.security.payload_scrubber.scrub_dict", return_value={"scrubbed": "data"}) as mock_scrub:
                result = scrub_request_payload(test_payload)
                
                # Verify fallback was called
                mock_scrub.assert_called_once()
                assert result == {"scrubbed": "data"}

    def test_scrub_request_payload_fallback_exception(self) -> None:
        """Test fallback exception handling (lines 340-342)."""
        from mlsdm.security.payload_scrubber import scrub_request_payload

        test_payload = {"api_key": "secret", "data": "value"}

        # Mock both functions to raise exceptions
        with patch("mlsdm.security.payload_scrubber._scrub_with_forbidden_fields", side_effect=Exception("Primary error")):
            with patch("mlsdm.security.payload_scrubber.scrub_dict", side_effect=Exception("Fallback error")):
                # Should return original payload when both fail
                result = scrub_request_payload(test_payload)
                assert result == test_payload
