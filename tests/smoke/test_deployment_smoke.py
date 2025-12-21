import os
import pytest
import requests
import time
from typing import Optional


class TestDeploymentSmoke:
    """Critical smoke tests for post-deployment validation"""

    BASE_URL: Optional[str] = None  # Set via env var
    TIMEOUT = 30  # seconds

    @classmethod
    def setup_class(cls):
        """Setup smoke test configuration"""
        cls.BASE_URL = os.getenv("SMOKE_TEST_URL", "http://localhost:8000")

        # Wait for service to be ready
        max_wait = 60
        start = time.time()
        while time.time() - start < max_wait:
            try:
                requests.get(f"{cls.BASE_URL}/health", timeout=5)
                break
            except requests.RequestException:
                time.sleep(2)
        else:
            pytest.fail(f"Service not ready after {max_wait}s")

    def test_health_endpoint_responds(self):
        """CRITICAL: Health endpoint must respond"""
        response = requests.get(f"{self.BASE_URL}/health", timeout=self.TIMEOUT)

        assert response.status_code == 200, f"Health check failed: {response.status_code}"

        data = response.json()
        assert data.get("status") == "healthy", f"Service unhealthy: {data}"

    def test_readiness_endpoint_ready(self):
        """CRITICAL: Readiness endpoint must be ready"""
        response = requests.get(f"{self.BASE_URL}/ready", timeout=self.TIMEOUT)

        assert response.status_code == 200, "Readiness check failed"

        data = response.json()
        assert data.get("ready") is True, f"Service not ready: {data}"

    def test_inference_endpoint_accessible(self):
        """CRITICAL: Main inference endpoint accessible"""
        response = requests.post(
            f"{self.BASE_URL}/v1/infer",
            json={"input": "test smoke input", "phase": "wake"},
            timeout=self.TIMEOUT,
        )

        # Accept 200 or auth errors (means endpoint works)
        assert response.status_code in [200, 401, 403], f"Inference endpoint broken: {response.status_code}"

    def test_metrics_endpoint_exports(self):
        """CRITICAL: Metrics endpoint must export"""
        response = requests.get(f"{self.BASE_URL}/metrics", timeout=self.TIMEOUT)

        assert response.status_code == 200, "Metrics endpoint failed"

        # Verify key metrics present
        metrics_text = response.text
        assert "mlsdm_" in metrics_text, "No ML-SDM metrics found"

    def test_api_version_matches(self):
        """CRITICAL: API version matches deployment"""
        expected_version = os.getenv("EXPECTED_VERSION", "1.2.0")

        response = requests.get(f"{self.BASE_URL}/version", timeout=self.TIMEOUT)

        assert response.status_code == 200
        data = response.json()

        assert data.get("version") == expected_version, f"Version mismatch: expected {expected_version}, got {data.get('version')}"

    def test_database_connectivity(self):
        """CRITICAL: Database must be accessible"""
        # Via health endpoint's DB check
        response = requests.get(f"{self.BASE_URL}/health", timeout=self.TIMEOUT)

        data = response.json()
        assert data.get("database") == "connected", f"Database not connected: {data.get('database')}"

    def test_memory_footprint_acceptable(self):
        """CRITICAL: Memory footprint within limits"""
        response = requests.get(f"{self.BASE_URL}/metrics", timeout=self.TIMEOUT)

        metrics = response.text

        # Parse memory metric (simplified)
        for line in metrics.split("\n"):
            if "process_resident_memory_bytes" in line and not line.startswith("#"):
                memory_bytes = float(line.split()[-1])
                memory_mb = memory_bytes / (1024 * 1024)

                # Fail if >500MB (something is very wrong)
                assert memory_mb < 500, f"Memory footprint too high: {memory_mb:.1f} MB"
                break

    def test_response_time_acceptable(self):
        """CRITICAL: Response time under SLO"""
        start = time.time()

        response = requests.post(
            f"{self.BASE_URL}/v1/infer",
            json={"input": "quick test", "phase": "wake"},
            timeout=self.TIMEOUT,
        )

        elapsed = time.time() - start

        # P99 should be <150ms, smoke test allows 500ms
        assert elapsed < 0.5, f"Response too slow: {elapsed:.3f}s"
