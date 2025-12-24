"""
E2E Subprocess Smoke Test for MLSDM Server.

This test verifies that the server can start and respond to health checks
in a subprocess. It uses proper anti-flake patterns:
- Ephemeral port allocation (avoids port conflicts)
- Polling with timeout (handles slow startup)
- Guaranteed process cleanup (terminate → kill)
- Isolation from external dependencies (uses local_stub backend)
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests


def find_free_port() -> int:
    """Find a free port by binding to port 0 and getting the assigned port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def wait_for_server(url: str, timeout: float = 30.0, interval: float = 0.5) -> bool:
    """Poll server health endpoint until it responds or timeout expires.

    Args:
        url: Health endpoint URL
        timeout: Maximum time to wait in seconds
        interval: Time between polls in seconds

    Returns:
        True if server responded, False if timeout expired
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2.0)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(interval)
    return False


def terminate_process(proc: subprocess.Popen, timeout: float = 5.0) -> None:
    """Gracefully terminate process, force kill if necessary.

    Args:
        proc: Process to terminate
        timeout: Time to wait for graceful shutdown before kill
    """
    if proc.poll() is not None:
        return  # Already terminated

    # Try graceful termination first
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        # Force kill if graceful termination failed
        proc.kill()
        proc.wait(timeout=2.0)


class TestServerSubprocessSmoke:
    """E2E tests that start the server in a subprocess."""

    @pytest.fixture
    def temp_config(self, tmp_path: Path) -> Path:
        """Use the default config file for testing.

        The default config is known to work and is properly validated.
        """
        return Path("config/default_config.yaml")

    @pytest.mark.slow
    def test_server_starts_and_responds_to_health(self, temp_config: Path) -> None:
        """Test that the server can start and respond to health checks."""
        port = find_free_port()
        health_url = f"http://127.0.0.1:{port}/health"

        # Clean environment - only set vars needed for the test
        # Use CLI serve directly to avoid runtime config setting MLSDM_* vars
        # that would be merged into config and cause validation failures
        env = os.environ.copy()
        env.update({
            "LLM_BACKEND": "local_stub",
            "DISABLE_RATE_LIMIT": "1",
            "OTEL_SDK_DISABLED": "true",
        })
        # Remove any MLSDM_* variables that might interfere with config validation
        keys_to_remove = [k for k in env if k.startswith("MLSDM_")]
        for key in keys_to_remove:
            del env[key]

        # Use CLI serve directly (doesn't call apply_runtime_config)
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "mlsdm.cli", "serve",
                "--host", "127.0.0.1",
                "--port", str(port),
                "--config", str(temp_config),
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            # Wait for server to start and respond
            server_ready = wait_for_server(health_url, timeout=30.0)
            assert server_ready, f"Server did not respond at {health_url} within timeout"

            # Verify health endpoint returns expected structure
            response = requests.get(health_url, timeout=5.0)
            assert response.status_code == 200

            # Also verify readiness endpoint
            readiness_url = f"http://127.0.0.1:{port}/health/readiness"
            response = requests.get(readiness_url, timeout=5.0)
            assert response.status_code == 200

        finally:
            # Guaranteed cleanup
            terminate_process(proc)

    @pytest.mark.slow
    def test_server_accepts_generate_request(self, temp_config: Path) -> None:
        """Test that the server can accept and process a generate request."""
        port = find_free_port()
        generate_url = f"http://127.0.0.1:{port}/generate"
        health_url = f"http://127.0.0.1:{port}/health"

        # Clean environment - only set vars needed for the test
        env = os.environ.copy()
        env.update({
            "LLM_BACKEND": "local_stub",
            "DISABLE_RATE_LIMIT": "1",
            "OTEL_SDK_DISABLED": "true",
        })
        # Remove any MLSDM_* variables that might interfere with config validation
        keys_to_remove = [k for k in env if k.startswith("MLSDM_")]
        for key in keys_to_remove:
            del env[key]

        # Use CLI serve directly
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "mlsdm.cli", "serve",
                "--host", "127.0.0.1",
                "--port", str(port),
                "--config", str(temp_config),
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            # Wait for server to start
            assert wait_for_server(health_url, timeout=30.0), "Server did not start"

            # Send a generate request
            response = requests.post(
                generate_url,
                json={"prompt": "Hello, world!"},
                timeout=10.0,
            )
            assert response.status_code == 200

            data = response.json()
            assert "response" in data
            assert "phase" in data
            assert "accepted" in data

        finally:
            terminate_process(proc)

    @pytest.mark.slow
    def test_server_with_cli_entrypoint(self, temp_config: Path) -> None:
        """Test that the server can be started via CLI entrypoint with custom config."""
        port = find_free_port()
        health_url = f"http://127.0.0.1:{port}/health"

        # Clean environment - only set vars needed for the test
        env = os.environ.copy()
        env.update({
            "LLM_BACKEND": "local_stub",
            "DISABLE_RATE_LIMIT": "1",
            "OTEL_SDK_DISABLED": "true",
        })
        # Remove any MLSDM_* variables that might interfere with config validation
        keys_to_remove = [k for k in env if k.startswith("MLSDM_")]
        for key in keys_to_remove:
            del env[key]

        # Use mlsdm CLI with serve command and custom port
        proc = subprocess.Popen(
            [
                sys.executable, "-m", "mlsdm.cli", "serve",
                "--host", "127.0.0.1",
                "--port", str(port),
                "--config", str(temp_config),
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        try:
            # Wait for server to start
            server_ready = wait_for_server(health_url, timeout=30.0)
            assert server_ready, f"CLI-started server did not respond at {health_url}"

            # Verify health endpoint
            response = requests.get(health_url, timeout=5.0)
            assert response.status_code == 200

        finally:
            terminate_process(proc)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "slow"])
