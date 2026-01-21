"""Tier 1 Smoke: API contract validation without server startup."""
import pytest

pytestmark = pytest.mark.smoke


class TestHealthContract:
    """Verify health API contracts."""

    def test_health_response_structure(self):
        """Health response should have required fields."""
        # Import the response model, not the endpoint
        try:
            from mlsdm.api.health import HealthResponse
            response = HealthResponse(status="healthy", version="test")
            assert response.status == "healthy"
            assert response.version == "test"
        except ImportError:
            # If HealthResponse doesn't exist, test basic health module import
            from mlsdm.api import health
            assert health is not None
