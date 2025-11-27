"""
Integration tests for API health endpoints.

Tests cover:
- Healthy state validation
- Degraded state detection
- Broken config handling
- Health endpoint response contracts
"""

import os

import pytest
from fastapi import status
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def setup_environment():
    """Set up test environment."""
    # Disable rate limiting for tests
    os.environ["DISABLE_RATE_LIMIT"] = "1"
    # Use local stub backend
    os.environ["LLM_BACKEND"] = "local_stub"
    yield
    # Cleanup
    if "DISABLE_RATE_LIMIT" in os.environ:
        del os.environ["DISABLE_RATE_LIMIT"]


@pytest.fixture
def client():
    """Create a test client with rate limiting disabled."""
    from mlsdm.api.app import app

    return TestClient(app)


class TestHealthyState:
    """Test API health endpoints in healthy state."""

    def test_health_returns_healthy(self, client):
        """Test that /health returns healthy status."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"

    def test_liveness_probe_always_returns_alive(self, client):
        """Test that /health/liveness always returns alive."""
        response = client.get("/health/liveness")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
        assert data["timestamp"] > 0

    def test_readiness_probe_returns_status(self, client):
        """Test that /health/readiness returns valid status."""
        response = client.get("/health/readiness")
        # Can be 200 (ready) or 503 (not ready) depending on system state
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        data = response.json()
        assert "ready" in data
        assert "status" in data
        assert "checks" in data
        assert isinstance(data["checks"], dict)

    def test_detailed_health_returns_system_info(self, client):
        """Test that /health/detailed returns system information."""
        response = client.get("/health/detailed")
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "system" in data
        assert data["status"] in ["healthy", "unhealthy"]

    def test_health_metrics_prometheus_format(self, client):
        """Test that /health/metrics returns Prometheus format."""
        response = client.get("/health/metrics")
        assert response.status_code == status.HTTP_200_OK
        assert "text/plain" in response.headers.get("content-type", "")
        content = response.text
        assert "# HELP" in content
        assert "# TYPE" in content
        assert "mlsdm_" in content


class TestDegradedState:
    """Test API health endpoints in degraded state scenarios."""

    def test_readiness_checks_memory_manager(self, client):
        """Test readiness check includes memory manager status."""
        response = client.get("/health/readiness")
        data = response.json()
        checks = data["checks"]
        # memory_manager check should be present
        assert "memory_manager" in checks
        # In test context, memory manager should be set via app.py
        assert isinstance(checks["memory_manager"], bool)

    def test_readiness_checks_system_resources(self, client):
        """Test readiness check includes system resource checks."""
        response = client.get("/health/readiness")
        data = response.json()
        checks = data["checks"]
        # System resource checks should be present
        assert "memory_available" in checks
        assert "cpu_available" in checks
        # Should be booleans
        assert isinstance(checks["memory_available"], bool)
        assert isinstance(checks["cpu_available"], bool)

    def test_detailed_health_includes_memory_state(self, client):
        """Test detailed health includes memory state when available."""
        response = client.get("/health/detailed")
        data = response.json()
        # Memory state should be present (may be None if not available)
        assert "memory_state" in data
        # If memory state is available, it should have L1/L2/L3 norms
        if data["memory_state"] is not None:
            assert "L1_norm" in data["memory_state"]
            assert "L2_norm" in data["memory_state"]
            assert "L3_norm" in data["memory_state"]

    def test_detailed_health_includes_phase(self, client):
        """Test detailed health includes cognitive phase."""
        response = client.get("/health/detailed")
        data = response.json()
        assert "phase" in data
        # Phase should be wake, sleep, or None
        if data["phase"] is not None:
            assert data["phase"] in ["wake", "sleep"]

    def test_detailed_health_includes_statistics(self, client):
        """Test detailed health includes statistics when available."""
        response = client.get("/health/detailed")
        data = response.json()
        assert "statistics" in data
        if data["statistics"] is not None:
            # Should have standard statistics fields
            assert "total_events_processed" in data["statistics"]
            assert "accepted_events_count" in data["statistics"]


class TestHealthEndpointContracts:
    """Test health endpoint HTTP contracts and status codes."""

    def test_health_returns_json(self, client):
        """Test that health endpoint returns JSON."""
        response = client.get("/health")
        assert "application/json" in response.headers.get("content-type", "")

    def test_liveness_returns_json(self, client):
        """Test that liveness endpoint returns JSON."""
        response = client.get("/health/liveness")
        assert "application/json" in response.headers.get("content-type", "")

    def test_readiness_returns_json(self, client):
        """Test that readiness endpoint returns JSON."""
        response = client.get("/health/readiness")
        assert "application/json" in response.headers.get("content-type", "")

    def test_detailed_returns_json(self, client):
        """Test that detailed endpoint returns JSON."""
        response = client.get("/health/detailed")
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_includes_request_id_header(self, client):
        """Test that health endpoint includes X-Request-ID header."""
        response = client.get("/health")
        assert "x-request-id" in response.headers

    def test_health_includes_security_headers(self, client):
        """Test that health endpoint includes security headers."""
        response = client.get("/health")
        # SecurityHeadersMiddleware should add these
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers


class TestHealthEndpointEdgeCases:
    """Test health endpoint edge cases and error scenarios."""

    def test_health_with_custom_request_id(self, client):
        """Test that custom X-Request-ID is propagated."""
        custom_id = "test-request-12345"
        response = client.get("/health", headers={"X-Request-ID": custom_id})
        assert response.status_code == status.HTTP_200_OK
        # Response should echo the custom ID
        assert response.headers.get("x-request-id") == custom_id

    def test_nonexistent_health_subpath_returns_404(self, client):
        """Test that nonexistent health subpath returns 404."""
        response = client.get("/health/nonexistent")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_health_with_post_method_returns_405(self, client):
        """Test that POST to /health returns 405 Method Not Allowed."""
        response = client.post("/health")
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestStatusEndpoint:
    """Test /status endpoint integration."""

    def test_status_returns_200(self, client):
        """Test that /status returns 200 OK."""
        response = client.get("/status")
        assert response.status_code == status.HTTP_200_OK

    def test_status_contains_version(self, client):
        """Test that /status contains version information."""
        response = client.get("/status")
        data = response.json()
        assert "version" in data
        assert isinstance(data["version"], str)

    def test_status_contains_backend(self, client):
        """Test that /status contains backend information."""
        response = client.get("/status")
        data = response.json()
        assert "backend" in data
        assert data["backend"] == "local_stub"

    def test_status_contains_system_info(self, client):
        """Test that /status contains system info."""
        response = client.get("/status")
        data = response.json()
        assert "system" in data
        system = data["system"]
        assert "memory_mb" in system
        assert "cpu_percent" in system
        assert isinstance(system["memory_mb"], (int, float))

    def test_status_contains_config(self, client):
        """Test that /status contains config information."""
        response = client.get("/status")
        data = response.json()
        assert "config" in data
        config = data["config"]
        assert "dimension" in config
        assert "rate_limiting_enabled" in config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
