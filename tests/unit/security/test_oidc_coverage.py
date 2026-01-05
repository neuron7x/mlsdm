"""Additional OIDC coverage tests for uncovered branches.

Tests target specific uncovered code paths in oidc.py lines 326-372, 441-461.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.exceptions import HTTPException


class TestOIDCAuthenticatorExceptionHandling:
    """Test OIDC authenticator exception handling paths."""

    @pytest.mark.asyncio
    async def test_authenticate_jwt_validation_error_path(self) -> None:
        """Test JWT validation error handling (lines 370-376)."""
        from mlsdm.security.oidc import OIDCAuthenticator, OIDCConfig

        config = OIDCConfig(
            enabled=True,
            issuer="https://issuer.example.com",
            audience="test-audience",
        )
        authenticator = OIDCAuthenticator(config)

        # Mock request with token
        request = MagicMock(spec=Request)
        request.headers = {"Authorization": "Bearer invalid-token"}

        # Mock jwt module to be available but fail validation
        mock_jwt = MagicMock()
        mock_jwt.decode.side_effect = Exception("Token validation failed")
        
        with patch("mlsdm.security.oidc.OIDCAuthenticator._extract_token", return_value="invalid-token"):
            with patch("mlsdm.security.oidc.OIDCAuthenticator._get_jwks_uri", return_value="https://jwks.example.com"):
                # Make jwt importable but have decode fail
                with patch.dict("sys.modules", {"jwt": mock_jwt}):
                    with pytest.raises(HTTPException) as exc_info:
                        await authenticator.authenticate(request)

                    assert exc_info.value.status_code == 401
                    assert "Invalid or expired token" in str(exc_info.value.detail)


class TestOIDCAuthMiddlewareExceptionHandling:
    """Test OIDC middleware exception handling paths."""

    @pytest.mark.asyncio
    async def test_middleware_general_exception_path(self) -> None:
        """Test middleware general exception handling (lines 457-460)."""
        from mlsdm.security.oidc import OIDCAuthMiddleware, OIDCAuthenticator, OIDCConfig

        config = OIDCConfig(enabled=True, issuer="https://issuer.example.com", audience="test-audience")
        authenticator = OIDCAuthenticator(config)
        middleware = OIDCAuthMiddleware(app=MagicMock(), authenticator=authenticator)

        # Mock request
        request = MagicMock(spec=Request)
        request.url.path = "/test"
        request.state = MagicMock()
        
        # Mock authenticator to raise a non-HTTPException
        async def mock_auth_error(req):
            raise RuntimeError("Unexpected error")
        
        with patch.object(authenticator, "authenticate", side_effect=mock_auth_error):
            # Mock call_next as async
            call_next = AsyncMock()
            call_next.return_value = MagicMock()

            # Should not raise, should set user_info to None
            result = await middleware.dispatch(request, call_next)
            
            # Verify user_info is set to None on error
            assert request.state.user_info is None
            # Verify call_next was still called
            call_next.assert_called_once_with(request)

    @pytest.mark.asyncio
    async def test_middleware_require_auth_paths_check(self) -> None:
        """Test middleware path authentication requirement (lines 446-453)."""
        from mlsdm.security.oidc import OIDCAuthMiddleware, OIDCAuthenticator, OIDCConfig

        config = OIDCConfig(enabled=True, issuer="https://issuer.example.com", audience="test-audience")
        authenticator = OIDCAuthenticator(config)
        middleware = OIDCAuthMiddleware(
            app=MagicMock(),
            authenticator=authenticator,
            require_auth_paths=["/api/protected"]
        )

        # Mock request to protected path
        request = MagicMock(spec=Request)
        request.url.path = "/api/protected/resource"
        request.state = MagicMock()
        
        # Mock authenticator to return None (no auth)
        async def mock_auth_none(req):
            return None
        
        with patch.object(authenticator, "authenticate", side_effect=mock_auth_none):
            call_next = AsyncMock()

            with pytest.raises(HTTPException) as exc_info:
                await middleware.dispatch(request, call_next)

            assert exc_info.value.status_code == 401
            assert "Authentication required" in str(exc_info.value.detail)

