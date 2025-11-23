"""
Pytest configuration and fixtures for mlsdm test suite.

Configures Hypothesis for deterministic property-based testing in CI.
"""

import os
from hypothesis import settings, HealthCheck

# Register Hypothesis CI profile for deterministic testing
settings.register_profile(
    "ci",
    max_examples=50,
    deadline=200,
    derandomize=True,
    print_blob=True,
    suppress_health_check=[HealthCheck.too_slow],
)

# Load CI profile if HYPOTHESIS_PROFILE is set to 'ci'
if os.environ.get("HYPOTHESIS_PROFILE") == "ci":
    settings.load_profile("ci")
