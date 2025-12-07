"""Dependency health checks.

This module verifies that critical dependencies are present in requirements files.
These tests act as guardrails to prevent accidental removal of essential packages.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def get_requirements_content(filename: str) -> str:
    """Read requirements file content.
    
    Args:
        filename: Name of the requirements file (e.g., 'requirements-dev.txt')
    
    Returns:
        Content of the requirements file
    
    Raises:
        FileNotFoundError: If the requirements file doesn't exist
    """
    repo_root = Path(__file__).parent.parent.parent
    req_file = repo_root / filename
    
    if not req_file.exists():
        raise FileNotFoundError(f"Requirements file not found: {req_file}")
    
    return req_file.read_text()


def check_package_in_requirements(content: str, package: str) -> bool:
    """Check if a package is mentioned in requirements content.
    
    Args:
        content: Content of requirements file
        package: Package name to search for (e.g., 'pytest', 'opentelemetry-sdk')
    
    Returns:
        True if package is found, False otherwise
    """
    # Check each line
    for line in content.splitlines():
        # Strip comments and whitespace
        line = line.split("#")[0].strip()
        
        # Skip empty lines and -r includes
        if not line or line.startswith("-r"):
            continue
        
        # Check if this line mentions the package
        # Handle various formats: package>=1.0, package==1.0, package
        if line.startswith(package):
            # Verify it's not a substring match (e.g., 'pytest' vs 'pytest-cov')
            if len(line) == len(package) or line[len(package)] in ">=<~!=":
                return True
    
    return False


class TestCoreDependencies:
    """Test that core dependencies are present in requirements.txt."""
    
    def test_requirements_txt_exists(self) -> None:
        """Verify requirements.txt exists."""
        repo_root = Path(__file__).parent.parent.parent
        req_file = repo_root / "requirements.txt"
        assert req_file.exists(), "requirements.txt not found"
    
    def test_numpy_in_requirements(self) -> None:
        """Verify numpy is in requirements.txt."""
        content = get_requirements_content("requirements.txt")
        assert check_package_in_requirements(content, "numpy"), \
            "numpy not found in requirements.txt"
    
    def test_fastapi_in_requirements(self) -> None:
        """Verify fastapi is in requirements.txt."""
        content = get_requirements_content("requirements.txt")
        assert check_package_in_requirements(content, "fastapi"), \
            "fastapi not found in requirements.txt"
    
    def test_pydantic_in_requirements(self) -> None:
        """Verify pydantic is in requirements.txt."""
        content = get_requirements_content("requirements.txt")
        assert check_package_in_requirements(content, "pydantic"), \
            "pydantic not found in requirements.txt"


class TestDevDependencies:
    """Test that development dependencies are present in requirements-dev.txt."""
    
    def test_requirements_dev_txt_exists(self) -> None:
        """Verify requirements-dev.txt exists."""
        repo_root = Path(__file__).parent.parent.parent
        req_file = repo_root / "requirements-dev.txt"
        assert req_file.exists(), "requirements-dev.txt not found"
    
    def test_pytest_in_dev_requirements(self) -> None:
        """Verify pytest is in requirements-dev.txt."""
        content = get_requirements_content("requirements-dev.txt")
        assert check_package_in_requirements(content, "pytest"), \
            "pytest not found in requirements-dev.txt - tests cannot run without it"
    
    def test_mypy_in_dev_requirements(self) -> None:
        """Verify mypy is in requirements-dev.txt."""
        content = get_requirements_content("requirements-dev.txt")
        assert check_package_in_requirements(content, "mypy"), \
            "mypy not found in requirements-dev.txt - type checking unavailable"
    
    def test_ruff_in_dev_requirements(self) -> None:
        """Verify ruff is in requirements-dev.txt."""
        content = get_requirements_content("requirements-dev.txt")
        assert check_package_in_requirements(content, "ruff"), \
            "ruff not found in requirements-dev.txt - linting unavailable"
    
    def test_hypothesis_in_dev_requirements(self) -> None:
        """Verify hypothesis is in requirements-dev.txt."""
        content = get_requirements_content("requirements-dev.txt")
        assert check_package_in_requirements(content, "hypothesis"), \
            "hypothesis not found in requirements-dev.txt - property tests unavailable"


class TestObservabilityDependencies:
    """Test that observability dependencies are properly configured."""
    
    def test_opentelemetry_in_dev_requirements(self) -> None:
        """Verify opentelemetry packages are in requirements-dev.txt.
        
        OTEL is optional at runtime but required in dev for testing tracing.
        """
        content = get_requirements_content("requirements-dev.txt")
        # Check for any OTEL package
        has_otel = any(
            "opentelemetry" in line.lower()
            for line in content.splitlines()
            if not line.strip().startswith("#") and line.strip()
        )
        
        assert has_otel, \
            "opentelemetry packages not found in requirements-dev.txt"
    
    def test_opentelemetry_not_required_in_core(self) -> None:
        """Verify opentelemetry is NOT hard-required in requirements.txt.
        
        OTEL should be optional - core functionality must work without it.
        """
        content = get_requirements_content("requirements.txt")
        
        # Check that OTEL is not uncommented/required
        lines_with_otel = []
        for line in content.splitlines():
            # Skip comments
            if line.strip().startswith("#"):
                continue
            clean_line = line.split("#")[0].strip()
            if clean_line and "opentelemetry" in clean_line.lower():
                lines_with_otel.append(line)
        
        # OTEL should not be in uncommented lines
        assert len(lines_with_otel) == 0, \
            f"opentelemetry should not be required in core requirements.txt. Found: {lines_with_otel}"
    
    def test_prometheus_client_in_requirements(self) -> None:
        """Verify prometheus-client is in requirements.txt.
        
        Prometheus metrics are core functionality, not optional.
        """
        content = get_requirements_content("requirements.txt")
        assert check_package_in_requirements(content, "prometheus-client"), \
            "prometheus-client not found in requirements.txt"


class TestRequirementsStructure:
    """Test the structure and organization of requirements files."""
    
    def test_dev_requirements_includes_core(self) -> None:
        """Verify requirements-dev.txt includes requirements.txt."""
        content = get_requirements_content("requirements-dev.txt")
        
        # Should have -r requirements.txt line
        has_include = False
        for line in content.splitlines():
            clean_line = line.strip()
            if clean_line.startswith("-r") and "requirements.txt" in clean_line:
                has_include = True
                break
        
        assert has_include, \
            "requirements-dev.txt should include requirements.txt with -r"
