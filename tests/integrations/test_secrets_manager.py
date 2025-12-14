"""
Tests for secrets manager integration.
"""

import os
from unittest.mock import MagicMock, patch

import pytest

from mlsdm.integrations import SecretProvider, SecretsManager


class TestSecretsManager:
    """Test secrets manager integration."""

    def test_initialization(self) -> None:
        """Test manager initialization."""
        manager = SecretsManager(
            provider=SecretProvider.VAULT,
            vault_addr="https://vault.example.com",
            vault_token="s.test",
        )

        assert manager.provider == SecretProvider.VAULT
        assert manager.vault_addr == "https://vault.example.com"
        assert manager.vault_token == "s.test"

    def test_get_secret_from_environment(self) -> None:
        """Test retrieving secret from environment."""
        manager = SecretsManager(provider=SecretProvider.ENVIRONMENT)

        with patch.dict(os.environ, {"TEST_SECRET": "test_value"}):
            secret = manager.get_secret("TEST_SECRET")
            assert secret == "test_value"

    def test_get_secret_with_default(self) -> None:
        """Test default value when secret not found."""
        manager = SecretsManager(provider=SecretProvider.ENVIRONMENT)

        secret = manager.get_secret("NONEXISTENT_KEY", default="default_value")
        assert secret == "default_value"

    def test_get_secret_from_vault_success(self) -> None:
        """Test retrieving secret from Vault."""
        manager = SecretsManager(
            provider=SecretProvider.VAULT,
            vault_addr="https://vault.example.com",
            vault_token="s.test",
        )

        mock_response = {"data": {"data": {"value": "secret_from_vault"}}}

        with patch("requests.get") as mock_get:
            mock_get.return_value.json.return_value = mock_response
            mock_get.return_value.raise_for_status = MagicMock()

            secret = manager.get_secret("myapp/api_key")
            assert secret == "secret_from_vault"

    def test_cache_functionality(self) -> None:
        """Test that secrets are cached."""
        manager = SecretsManager(provider=SecretProvider.ENVIRONMENT)

        with patch.dict(os.environ, {"CACHED_SECRET": "cached_value"}):
            # First call - should cache
            secret1 = manager.get_secret("CACHED_SECRET")
            
            # Clear environment
            os.environ.pop("CACHED_SECRET", None)
            
            # Second call - should return cached value
            secret2 = manager.get_secret("CACHED_SECRET")
            
            assert secret1 == "cached_value"
            assert secret2 == "cached_value"

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        manager = SecretsManager(provider=SecretProvider.ENVIRONMENT)

        with patch.dict(os.environ, {"TEST_KEY": "test"}):
            manager.get_secret("TEST_KEY")
            assert "TEST_KEY" in manager._cache

            manager.clear_cache()
            assert len(manager._cache) == 0

    def test_invalid_secret_name_injection_prevention(self) -> None:
        """Test that invalid secret names are rejected to prevent injection."""
        manager = SecretsManager(provider=SecretProvider.ENVIRONMENT)

        # Test various injection attempts
        invalid_names = [
            "../../../etc/passwd",  # Path traversal
            "secret; rm -rf /",  # Command injection
            "secret && malicious",  # Command chaining
            "secret | cat",  # Pipe injection
            "secret`whoami`",  # Command substitution
            "secret$(whoami)",  # Command substitution
            "secret<script>",  # Script injection
            "secret\x00null",  # Null byte injection
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="Invalid secret name format"):
                manager.get_secret(invalid_name)

    def test_valid_secret_names(self) -> None:
        """Test that valid secret names are accepted."""
        manager = SecretsManager(provider=SecretProvider.ENVIRONMENT)

        valid_names = [
            "simple_secret",
            "app/api_key",
            "mlsdm/openai_api_key",
            "my-app/db-password",
            "service.config.key",
            "APP_SECRET_123",
        ]

        for valid_name in valid_names:
            # Should not raise ValueError
            with patch.dict(os.environ, {valid_name: "test"}):
                result = manager.get_secret(valid_name, default="default")
                # Either returns the value or default, but doesn't raise
                assert result in ["test", "default"]
