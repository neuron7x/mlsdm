"""Tests for API Authentication and RBAC.

This test suite validates the Role-Based Access Control (RBAC) system
including role validation, permission checking, and middleware behavior.
"""

import os
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

from mlsdm.security.rbac import (
    APIKeyConfig,
    Role,
    RoleValidator,
    UserContext,
    RBACMiddleware,
    get_role_validator,
    require_role,
    reset_role_validator,
    ROLE_HIERARCHY,
)


class TestRoleEnum:
    """Tests for Role enum."""

    def test_role_values(self):
        """Test that Role enum has expected values."""
        assert Role.READ.value == "read"
        assert Role.WRITE.value == "write"
        assert Role.ADMIN.value == "admin"

    def test_role_hierarchy_structure(self):
        """Test that role hierarchy is properly defined."""
        assert Role.READ in ROLE_HIERARCHY[Role.READ]
        assert Role.READ in ROLE_HIERARCHY[Role.WRITE]
        assert Role.WRITE in ROLE_HIERARCHY[Role.WRITE]
        assert Role.READ in ROLE_HIERARCHY[Role.ADMIN]
        assert Role.WRITE in ROLE_HIERARCHY[Role.ADMIN]
        assert Role.ADMIN in ROLE_HIERARCHY[Role.ADMIN]


class TestUserContext:
    """Tests for UserContext."""

    def test_user_context_creation(self):
        """Test UserContext can be created with required fields."""
        ctx = UserContext(
            user_id="user-123",
            roles={Role.READ, Role.WRITE},
        )
        assert ctx.user_id == "user-123"
        assert Role.READ in ctx.roles
        assert Role.WRITE in ctx.roles

    def test_has_role_direct(self):
        """Test has_role for directly assigned role."""
        ctx = UserContext(user_id="user-1", roles={Role.READ})
        assert ctx.has_role(Role.READ)
        assert not ctx.has_role(Role.WRITE)
        assert not ctx.has_role(Role.ADMIN)

    def test_has_role_hierarchical(self):
        """Test has_role respects hierarchy (admin has all permissions)."""
        ctx = UserContext(user_id="admin-1", roles={Role.ADMIN})
        assert ctx.has_role(Role.READ)
        assert ctx.has_role(Role.WRITE)
        assert ctx.has_role(Role.ADMIN)

    def test_has_role_write_includes_read(self):
        """Test that write role includes read permission."""
        ctx = UserContext(user_id="user-1", roles={Role.WRITE})
        assert ctx.has_role(Role.READ)
        assert ctx.has_role(Role.WRITE)
        assert not ctx.has_role(Role.ADMIN)

    def test_has_any_role(self):
        """Test has_any_role with multiple roles."""
        ctx = UserContext(user_id="user-1", roles={Role.READ})
        assert ctx.has_any_role([Role.READ, Role.WRITE])
        assert ctx.has_any_role([Role.READ])
        assert not ctx.has_any_role([Role.ADMIN])

    def test_is_expired_no_expiration(self):
        """Test is_expired when no expiration set."""
        ctx = UserContext(user_id="user-1", roles={Role.READ})
        assert not ctx.is_expired()

    def test_is_expired_future(self):
        """Test is_expired with future expiration."""
        ctx = UserContext(
            user_id="user-1",
            roles={Role.READ},
            expires_at=time.time() + 3600,  # 1 hour from now
        )
        assert not ctx.is_expired()

    def test_is_expired_past(self):
        """Test is_expired with past expiration."""
        ctx = UserContext(
            user_id="user-1",
            roles={Role.READ},
            expires_at=time.time() - 3600,  # 1 hour ago
        )
        assert ctx.is_expired()


class TestRoleValidator:
    """Tests for RoleValidator."""

    def setup_method(self):
        """Reset global validator before each test."""
        reset_role_validator()

    def test_add_and_validate_key(self):
        """Test adding and validating an API key."""
        validator = RoleValidator()
        validator.add_key("test-key-123", [Role.WRITE], "user-1")
        
        ctx = validator.validate_key("test-key-123")
        assert ctx is not None
        assert ctx.user_id == "user-1"
        assert Role.WRITE in ctx.roles

    def test_invalid_key_returns_none(self):
        """Test that invalid key returns None."""
        validator = RoleValidator()
        ctx = validator.validate_key("nonexistent-key")
        assert ctx is None

    def test_expired_key_returns_none(self):
        """Test that expired key returns None."""
        validator = RoleValidator()
        validator.add_key(
            "expired-key",
            [Role.READ],
            "user-1",
            expires_at=time.time() - 3600,  # 1 hour ago
        )
        
        ctx = validator.validate_key("expired-key")
        assert ctx is None

    def test_remove_key(self):
        """Test removing an API key."""
        validator = RoleValidator()
        validator.add_key("temp-key", [Role.READ], "user-1")
        
        assert validator.validate_key("temp-key") is not None
        
        removed = validator.remove_key("temp-key")
        assert removed
        
        assert validator.validate_key("temp-key") is None

    def test_remove_nonexistent_key(self):
        """Test removing a nonexistent key."""
        validator = RoleValidator()
        removed = validator.remove_key("nonexistent")
        assert not removed

    def test_get_key_count(self):
        """Test getting the number of registered keys."""
        validator = RoleValidator()
        initial_count = validator.get_key_count()
        
        validator.add_key("key-1", [Role.READ], "user-1")
        validator.add_key("key-2", [Role.WRITE], "user-2")
        
        assert validator.get_key_count() == initial_count + 2

    @patch.dict(os.environ, {"API_KEY": "env-api-key", "ADMIN_API_KEY": "admin-key"})
    def test_load_from_env(self):
        """Test loading keys from environment variables."""
        reset_role_validator()
        validator = RoleValidator()
        
        # Default API key should have write role
        ctx = validator.validate_key("env-api-key")
        assert ctx is not None
        assert ctx.has_role(Role.WRITE)
        
        # Admin key should have admin role
        ctx = validator.validate_key("admin-key")
        assert ctx is not None
        assert ctx.has_role(Role.ADMIN)


class TestRBACMiddleware:
    """Tests for RBACMiddleware."""

    def setup_method(self):
        """Set up test app and client."""
        reset_role_validator()
        self.app = FastAPI()
        
        # Add a test endpoint
        @self.app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        @self.app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        @self.app.post("/admin/reset")
        async def admin_reset():
            return {"status": "reset"}
        
        # Add RBAC middleware
        validator = RoleValidator()
        validator.add_key("read-key", [Role.READ], "reader")
        validator.add_key("write-key", [Role.WRITE], "writer")
        validator.add_key("admin-key", [Role.ADMIN], "admin")
        
        self.app.add_middleware(RBACMiddleware, role_validator=validator)
        self.client = TestClient(self.app)

    def test_health_endpoint_skips_auth(self):
        """Test that health endpoint skips RBAC."""
        response = self.client.get("/health")
        assert response.status_code == 200

    def test_missing_token_returns_401(self):
        """Test that missing token returns 401."""
        response = self.client.get("/test")
        assert response.status_code == 401
        assert "authentication" in response.json()["error"]["message"].lower()

    def test_invalid_token_returns_401(self):
        """Test that invalid token returns 401."""
        response = self.client.get(
            "/test",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    def test_valid_token_with_sufficient_role(self):
        """Test that valid token with sufficient role succeeds."""
        response = self.client.get(
            "/test",
            headers={"Authorization": "Bearer write-key"}
        )
        assert response.status_code == 200

    def test_valid_token_with_insufficient_role(self):
        """Test that valid token with insufficient role returns 403."""
        response = self.client.post(
            "/admin/reset",
            headers={"Authorization": "Bearer write-key"}
        )
        assert response.status_code == 403

    def test_admin_token_has_full_access(self):
        """Test that admin token has full access."""
        response = self.client.post(
            "/admin/reset",
            headers={"Authorization": "Bearer admin-key"}
        )
        assert response.status_code == 200

    def test_x_api_key_header_works(self):
        """Test that X-API-Key header works."""
        response = self.client.get(
            "/test",
            headers={"X-API-Key": "write-key"}
        )
        assert response.status_code == 200


class TestRequireRoleDecorator:
    """Tests for require_role decorator."""

    def setup_method(self):
        """Set up test app."""
        reset_role_validator()
        self.app = FastAPI()
        
        @self.app.get("/admin-only")
        @require_role(["admin"])
        async def admin_only(request: Request):
            return {"status": "admin"}
        
        @self.app.get("/write-or-admin")
        @require_role(["write", "admin"])
        async def write_or_admin(request: Request):
            return {"status": "write"}
        
        # Add validator and middleware
        validator = RoleValidator()
        validator.add_key("read-key", [Role.READ], "reader")
        validator.add_key("write-key", [Role.WRITE], "writer")
        validator.add_key("admin-key", [Role.ADMIN], "admin")
        
        self.app.add_middleware(RBACMiddleware, role_validator=validator)
        self.client = TestClient(self.app)

    def test_require_role_blocks_insufficient(self):
        """Test that require_role blocks users with insufficient permissions."""
        response = self.client.get(
            "/admin-only",
            headers={"Authorization": "Bearer write-key"}
        )
        assert response.status_code == 403

    def test_require_role_allows_sufficient(self):
        """Test that require_role allows users with sufficient permissions."""
        response = self.client.get(
            "/admin-only",
            headers={"Authorization": "Bearer admin-key"}
        )
        assert response.status_code == 200

    def test_require_role_with_multiple_roles(self):
        """Test require_role with multiple allowed roles."""
        response = self.client.get(
            "/write-or-admin",
            headers={"Authorization": "Bearer write-key"}
        )
        assert response.status_code == 200


class TestAPIKeyConfig:
    """Tests for APIKeyConfig dataclass."""

    def test_api_key_config_creation(self):
        """Test APIKeyConfig creation with all fields."""
        config = APIKeyConfig(
            key_hash="abc123",
            roles={Role.READ, Role.WRITE},
            user_id="user-1",
            expires_at=None,
            description="Test key",
            rate_limit=10.0,
        )
        assert config.key_hash == "abc123"
        assert Role.READ in config.roles
        assert config.user_id == "user-1"
        assert config.rate_limit == 10.0


class TestGlobalValidator:
    """Tests for global validator singleton."""

    def test_get_role_validator_singleton(self):
        """Test that get_role_validator returns singleton."""
        reset_role_validator()
        v1 = get_role_validator()
        v2 = get_role_validator()
        assert v1 is v2

    def test_reset_role_validator(self):
        """Test that reset_role_validator creates new instance."""
        v1 = get_role_validator()
        reset_role_validator()
        v2 = get_role_validator()
        assert v1 is not v2


class TestSecurityIntegration:
    """Integration tests for security features."""

    def test_without_key_401(self):
        """Test that requests without API key get 401."""
        reset_role_validator()
        app = FastAPI()
        
        @app.get("/protected")
        async def protected():
            return {"data": "secret"}
        
        validator = RoleValidator()
        validator.add_key("test-key", [Role.READ], "user-1")
        app.add_middleware(RBACMiddleware, role_validator=validator)
        
        client = TestClient(app)
        response = client.get("/protected")
        assert response.status_code == 401

    def test_valid_key_with_role(self):
        """Test that valid key with correct role succeeds."""
        reset_role_validator()
        app = FastAPI()
        
        @app.get("/protected")
        async def protected():
            return {"data": "secret"}
        
        validator = RoleValidator()
        validator.add_key("test-key", [Role.WRITE], "user-1")
        app.add_middleware(RBACMiddleware, role_validator=validator)
        
        client = TestClient(app)
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer test-key"}
        )
        assert response.status_code == 200
        assert response.json()["data"] == "secret"

    def test_negated_role_403(self):
        """Test that contrafactual role returns 403."""
        reset_role_validator()
        app = FastAPI()
        
        @app.get("/admin")
        async def admin_endpoint():
            return {"data": "admin-only"}
        
        validator = RoleValidator()
        validator.add_key("read-key", [Role.READ], "reader")
        app.add_middleware(
            RBACMiddleware,
            role_validator=validator,
            endpoint_permissions={"/admin": {Role.ADMIN}},
        )
        
        client = TestClient(app)
        response = client.get(
            "/admin",
            headers={"Authorization": "Bearer read-key"}
        )
        assert response.status_code == 403
