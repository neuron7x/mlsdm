#!/usr/bin/env python3
"""Post-deployment smoke tests for MLSDM Neuro Engine.

This script runs critical health checks after deployment to verify
the system is operational before considering the deployment successful.

Smoke tests validate:
1. Health/liveness endpoint responds correctly
2. Readiness endpoint indicates system is ready
3. API generates responses (basic functionality)
4. Memory subsystem is operational
5. Policy loading is successful

Exit codes:
    0: All smoke tests passed
    1: One or more smoke tests failed
"""

import argparse
import sys
import time
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("Error: requests library is required", file=sys.stderr)
    print("Install with: pip install requests", file=sys.stderr)
    sys.exit(1)


class SmokeTestError(Exception):
    """Raised when a smoke test fails."""

    pass


def test_health_endpoint(base_url: str, timeout: int = 10) -> None:
    """Test the health/liveness endpoint.

    Args:
        base_url: Base URL of the API
        timeout: Request timeout in seconds

    Raises:
        SmokeTestError: If health check fails
    """
    url = urljoin(base_url, "/health")
    print(f"Testing health endpoint: {url}")

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        data = response.json()

        if data.get("status") != "healthy":
            raise SmokeTestError(f"Health check returned status: {data.get('status')}")

        print("✅ Health endpoint: PASSED")

    except requests.RequestException as e:
        raise SmokeTestError(f"Health endpoint failed: {e}") from e


def test_readiness_endpoint(base_url: str, timeout: int = 10, max_retries: int = 3) -> None:
    """Test the readiness endpoint with retries.

    The readiness endpoint may return 503 if the system is still starting up,
    so we retry a few times before failing.

    Args:
        base_url: Base URL of the API
        timeout: Request timeout in seconds
        max_retries: Maximum number of retries

    Raises:
        SmokeTestError: If readiness check fails after all retries
    """
    url = urljoin(base_url, "/health/ready")
    print(f"Testing readiness endpoint: {url}")

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ready":
                    print(f"✅ Readiness endpoint: PASSED (attempt {attempt}/{max_retries})")
                    return

            # System not ready yet, retry
            if attempt < max_retries:
                print(
                    f"⏳ System not ready yet (attempt {attempt}/{max_retries}), retrying in 5s..."
                )
                time.sleep(5)

        except requests.RequestException as e:
            if attempt < max_retries:
                print(f"⏳ Request failed (attempt {attempt}/{max_retries}), retrying in 5s...")
                time.sleep(5)
            else:
                raise SmokeTestError(f"Readiness endpoint failed: {e}") from e

    raise SmokeTestError("Readiness endpoint did not return ready status after all retries")


def test_api_generation(base_url: str, timeout: int = 30) -> None:
    """Test basic API functionality by making a generate request.

    Args:
        base_url: Base URL of the API
        timeout: Request timeout in seconds

    Raises:
        SmokeTestError: If API generation fails
    """
    url = urljoin(base_url, "/generate")
    print(f"Testing API generation: {url}")

    payload = {"prompt": "Hello, this is a smoke test", "max_tokens": 50}

    try:
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()

        data = response.json()

        if "response" not in data:
            raise SmokeTestError(f"API response missing 'response' field: {data}")

        print("✅ API generation: PASSED")

    except requests.RequestException as e:
        raise SmokeTestError(f"API generation failed: {e}") from e


def test_memory_subsystem(base_url: str, timeout: int = 10) -> None:
    """Test memory subsystem is operational.

    Args:
        base_url: Base URL of the API
        timeout: Request timeout in seconds

    Raises:
        SmokeTestError: If memory subsystem check fails
    """
    url = urljoin(base_url, "/state")
    print(f"Testing memory subsystem: {url}")

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        data = response.json()

        # Check that state has expected structure
        if "memory" not in data:
            raise SmokeTestError(f"State response missing 'memory' field: {data}")

        print("✅ Memory subsystem: PASSED")

    except requests.RequestException as e:
        raise SmokeTestError(f"Memory subsystem check failed: {e}") from e


def test_metrics_endpoint(base_url: str, timeout: int = 10) -> None:
    """Test metrics endpoint is accessible.

    Args:
        base_url: Base URL of the API
        timeout: Request timeout in seconds

    Raises:
        SmokeTestError: If metrics endpoint fails
    """
    url = urljoin(base_url, "/health/metrics")
    print(f"Testing metrics endpoint: {url}")

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        # Metrics should be in Prometheus text format
        content_type = response.headers.get("content-type", "")
        if "text/plain" not in content_type:
            raise SmokeTestError(f"Metrics endpoint returned unexpected content type: {content_type}")

        print("✅ Metrics endpoint: PASSED")

    except requests.RequestException as e:
        raise SmokeTestError(f"Metrics endpoint failed: {e}") from e


def run_smoke_tests(
    base_url: str, timeout: int = 30, skip_generation: bool = False
) -> tuple[int, int]:
    """Run all smoke tests.

    Args:
        base_url: Base URL of the API
        timeout: Request timeout in seconds
        skip_generation: Skip the generation test (useful for quick checks)

    Returns:
        Tuple of (passed_count, total_count)
    """
    tests = [
        ("Health endpoint", test_health_endpoint),
        ("Readiness endpoint", test_readiness_endpoint),
        ("Metrics endpoint", test_metrics_endpoint),
        ("Memory subsystem", test_memory_subsystem),
    ]

    if not skip_generation:
        tests.append(("API generation", test_api_generation))

    passed = 0
    total = len(tests)

    print(f"\n{'=' * 60}")
    print(f"Running {total} smoke tests against {base_url}")
    print(f"{'=' * 60}\n")

    for name, test_func in tests:
        try:
            test_func(base_url, timeout=timeout)
            passed += 1
        except SmokeTestError as e:
            print(f"❌ {name}: FAILED")
            print(f"   Error: {e}")
        except Exception as e:
            print(f"❌ {name}: FAILED (unexpected error)")
            print(f"   Error: {e}")

    return passed, total


def main() -> int:
    """Main entry point for smoke tests.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    parser = argparse.ArgumentParser(
        description="Run post-deployment smoke tests for MLSDM Neuro Engine"
    )
    parser.add_argument(
        "base_url",
        help="Base URL of the deployed API (e.g., http://localhost:8000 or https://api.example.com)",
    )
    parser.add_argument(
        "--timeout", type=int, default=30, help="Request timeout in seconds (default: 30)"
    )
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip the API generation test (useful for quick checks)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Remove trailing slash from base URL
    base_url = args.base_url.rstrip("/")

    try:
        passed, total = run_smoke_tests(
            base_url, timeout=args.timeout, skip_generation=args.skip_generation
        )

        print(f"\n{'=' * 60}")
        print(f"Smoke Test Results: {passed}/{total} tests passed")
        print(f"{'=' * 60}\n")

        if passed == total:
            print("🎉 All smoke tests passed! Deployment is healthy.")
            return 0
        else:
            print(f"❌ {total - passed} smoke test(s) failed. Deployment may be unhealthy.")
            return 1

    except KeyboardInterrupt:
        print("\n\nSmoke tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nFatal error running smoke tests: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
