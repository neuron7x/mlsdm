"""Tests for smoke test script functionality."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add scripts directory to path for importing - done before importing smoke_test
# ruff: noqa: E402
scripts_dir = Path(__file__).parent.parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

# Import after adding to path
import smoke_test


class TestSmokeTests:
    """Test smoke test functions."""

    @patch("smoke_test.requests.get")
    def test_health_endpoint_success(self, mock_get: Mock) -> None:
        """Test successful health endpoint check."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Should not raise
        smoke_test.test_health_endpoint("http://test.com")

        mock_get.assert_called_once_with("http://test.com/health", timeout=10)

    @patch("smoke_test.requests.get")
    def test_health_endpoint_unhealthy(self, mock_get: Mock) -> None:
        """Test health endpoint check with unhealthy status."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "degraded"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(smoke_test.SmokeTestError, match="Health check returned status"):
            smoke_test.test_health_endpoint("http://test.com")

    @patch("smoke_test.requests.get")
    def test_readiness_endpoint_success(self, mock_get: Mock) -> None:
        """Test successful readiness endpoint check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ready"}
        mock_get.return_value = mock_response

        # Should not raise
        smoke_test.test_readiness_endpoint("http://test.com")

        mock_get.assert_called_once_with("http://test.com/health/ready", timeout=10)

    @patch("smoke_test.time.sleep")
    @patch("smoke_test.requests.get")
    def test_readiness_endpoint_retries(self, mock_get: Mock, mock_sleep: Mock) -> None:
        """Test readiness endpoint check with retries."""
        # First two attempts fail, third succeeds
        mock_response_fail = Mock()
        mock_response_fail.status_code = 503

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"status": "ready"}

        mock_get.side_effect = [mock_response_fail, mock_response_fail, mock_response_success]

        # Should not raise after retries
        smoke_test.test_readiness_endpoint("http://test.com")

        assert mock_get.call_count == 3
        assert mock_sleep.call_count == 2

    @patch("smoke_test.requests.post")
    def test_api_generation_success(self, mock_post: Mock) -> None:
        """Test successful API generation check."""
        mock_response = Mock()
        mock_response.json.return_value = {"response": "Test response"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Should not raise
        smoke_test.test_api_generation("http://test.com")

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "http://test.com/generate"
        assert "prompt" in kwargs["json"]

    @patch("smoke_test.requests.post")
    def test_api_generation_missing_response(self, mock_post: Mock) -> None:
        """Test API generation check with missing response field."""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "something went wrong"}
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        with pytest.raises(smoke_test.SmokeTestError, match="missing 'response' field"):
            smoke_test.test_api_generation("http://test.com")

    @patch("smoke_test.requests.get")
    def test_memory_subsystem_success(self, mock_get: Mock) -> None:
        """Test successful memory subsystem check."""
        mock_response = Mock()
        mock_response.json.return_value = {"memory": {"L1": {}, "L2": {}, "L3": {}}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Should not raise
        smoke_test.test_memory_subsystem("http://test.com")

        mock_get.assert_called_once_with("http://test.com/state", timeout=10)

    @patch("smoke_test.requests.get")
    def test_memory_subsystem_missing_memory(self, mock_get: Mock) -> None:
        """Test memory subsystem check with missing memory field."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with pytest.raises(smoke_test.SmokeTestError, match="missing 'memory' field"):
            smoke_test.test_memory_subsystem("http://test.com")

    @patch("smoke_test.requests.get")
    def test_metrics_endpoint_success(self, mock_get: Mock) -> None:
        """Test successful metrics endpoint check."""
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/plain; version=0.0.4"}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Should not raise
        smoke_test.test_metrics_endpoint("http://test.com")

        mock_get.assert_called_once_with("http://test.com/health/metrics", timeout=10)

    @patch("smoke_test.test_health_endpoint")
    @patch("smoke_test.test_readiness_endpoint")
    @patch("smoke_test.test_metrics_endpoint")
    @patch("smoke_test.test_memory_subsystem")
    @patch("smoke_test.test_api_generation")
    def test_run_smoke_tests_all_pass(
        self,
        mock_gen: Mock,
        mock_mem: Mock,
        mock_metrics: Mock,
        mock_ready: Mock,
        mock_health: Mock,
    ) -> None:
        """Test running all smoke tests successfully."""
        passed, total = smoke_test.run_smoke_tests("http://test.com")

        assert passed == total
        assert total == 5
        assert mock_health.called
        assert mock_ready.called
        assert mock_metrics.called
        assert mock_mem.called
        assert mock_gen.called

    @patch("smoke_test.test_health_endpoint")
    @patch("smoke_test.test_readiness_endpoint")
    @patch("smoke_test.test_metrics_endpoint")
    @patch("smoke_test.test_memory_subsystem")
    @patch("smoke_test.test_api_generation")
    def test_run_smoke_tests_skip_generation(
        self,
        mock_gen: Mock,
        mock_mem: Mock,
        mock_metrics: Mock,
        mock_ready: Mock,
        mock_health: Mock,
    ) -> None:
        """Test running smoke tests with generation skipped."""
        passed, total = smoke_test.run_smoke_tests("http://test.com", skip_generation=True)

        assert passed == total
        assert total == 4
        assert mock_health.called
        assert mock_ready.called
        assert mock_metrics.called
        assert mock_mem.called
        assert not mock_gen.called

    @patch("smoke_test.test_health_endpoint")
    @patch("smoke_test.test_readiness_endpoint")
    @patch("smoke_test.test_metrics_endpoint")
    @patch("smoke_test.test_memory_subsystem")
    @patch("smoke_test.test_api_generation")
    def test_run_smoke_tests_partial_failure(
        self,
        mock_gen: Mock,
        mock_mem: Mock,
        mock_metrics: Mock,
        mock_ready: Mock,
        mock_health: Mock,
    ) -> None:
        """Test running smoke tests with some failures."""
        # Make metrics and generation fail
        mock_metrics.side_effect = smoke_test.SmokeTestError("Metrics failed")
        mock_gen.side_effect = smoke_test.SmokeTestError("Generation failed")

        passed, total = smoke_test.run_smoke_tests("http://test.com")

        assert passed == 3
        assert total == 5


class TestMainFunction:
    """Test main entry point."""

    @patch("smoke_test.run_smoke_tests")
    @patch("sys.argv", ["smoke_test.py", "http://test.com"])
    def test_main_success(self, mock_run: Mock) -> None:
        """Test main function with successful tests."""
        mock_run.return_value = (5, 5)

        exit_code = smoke_test.main()

        assert exit_code == 0
        mock_run.assert_called_once()

    @patch("smoke_test.run_smoke_tests")
    @patch("sys.argv", ["smoke_test.py", "http://test.com"])
    def test_main_failure(self, mock_run: Mock) -> None:
        """Test main function with failed tests."""
        mock_run.return_value = (3, 5)

        exit_code = smoke_test.main()

        assert exit_code == 1
        mock_run.assert_called_once()

    @patch("smoke_test.run_smoke_tests")
    @patch("sys.argv", ["smoke_test.py", "http://test.com", "--skip-generation"])
    def test_main_with_skip_generation(self, mock_run: Mock) -> None:
        """Test main function with skip generation flag."""
        mock_run.return_value = (4, 4)

        exit_code = smoke_test.main()

        assert exit_code == 0
        args, kwargs = mock_run.call_args
        assert kwargs["skip_generation"] is True
