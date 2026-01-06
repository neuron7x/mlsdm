"""
Mutation testing configuration and fixtures.

This module provides configuration and fixtures for mutation testing
with mutmut. Mutation testing validates that tests can detect bugs
by introducing small code changes (mutants) and verifying tests fail.
"""

import pytest


@pytest.fixture
def mutation_config():
    """
    Configuration for mutation testing runs.
    
    Returns dict with:
    - target_paths: List of critical paths to mutate
    - mutation_score_threshold: Minimum acceptable mutation score (0.80)
    - timeout: Maximum seconds per mutant execution
    """
    return {
        "target_paths": [
            "src/mlsdm/cognition/moral_filter_v2.py",
            "src/mlsdm/memory/phase_entangled_lattice_memory.py",
            "src/mlsdm/core/cognitive_controller.py",
            "src/mlsdm/memory/multi_level_memory.py",
        ],
        "mutation_score_threshold": 0.80,
        "timeout": 10.0,
    }


@pytest.fixture
def critical_function_markers():
    """
    Markers for critical functions that must have high mutation coverage.
    
    Returns dict mapping module paths to critical function names.
    """
    return {
        "moral_filter_v2": ["evaluate", "adapt", "_clamp_threshold"],
        "phase_entangled_lattice_memory": ["entangle", "retrieve", "_check_capacity"],
        "cognitive_controller": ["process_event", "_check_emergency_shutdown"],
        "multi_level_memory": ["update", "_apply_decay"],
    }
