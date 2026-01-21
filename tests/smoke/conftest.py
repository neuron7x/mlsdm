"""Smoke test configuration with 60-second budget enforcement."""
import time

import pytest

_suite_start_time = None


def pytest_configure(config):
    """Register smoke test marker."""
    config.addinivalue_line(
        "markers", "smoke: Critical path smoke tests (<60s total)"
    )


@pytest.fixture(scope="session", autouse=True)
def enforce_smoke_budget():
    """Enforce 60-second budget for entire smoke suite."""
    global _suite_start_time
    _suite_start_time = time.monotonic()
    yield
    elapsed = time.monotonic() - _suite_start_time
    if elapsed > 60:
        pytest.fail(
            f"SMOKE BUDGET EXCEEDED: Suite took {elapsed:.1f}s (budget: 60s). "
            f"Move slow tests to tests/unit/ or optimize."
        )
