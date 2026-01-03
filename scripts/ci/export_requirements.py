#!/usr/bin/env python3
"""Export requirements.txt from pyproject.toml dependencies.

This script ensures requirements.txt stays in sync with pyproject.toml.
Run this to regenerate requirements.txt when dependencies change.

Usage:
    python scripts/ci/export_requirements.py
    python scripts/ci/export_requirements.py --check  # CI mode: fail if drift detected
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Project root is two levels up from this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"

GENERATED_HEADER = """\
# GENERATED FILE - DO NOT EDIT MANUALLY
# This file is auto-generated from pyproject.toml dependencies.
# Regenerate with: python scripts/ci/export_requirements.py
#
# MLSDM Full Installation Requirements
#
# This file includes ALL dependencies including optional ones.
# For minimal installation: pip install -e .
# For embeddings support: pip install -e ".[embeddings]"
# For full dev install: pip install -r requirements.txt
#
"""


def parse_pyproject_deps(content: str) -> dict[str, list[str]]:
    """Parse dependencies from pyproject.toml content.

    Returns a dict with keys:
    - 'core': main dependencies
    - 'embeddings': optional embeddings deps
    - 'observability': optional observability deps
    - 'dev': dev dependencies
    - 'visualization': optional visualization deps
    """
    deps: dict[str, list[str]] = {
        "core": [],
        "embeddings": [],
        "observability": [],
        "dev": [],
        "visualization": [],
    }

    # Parse core dependencies
    core_match = re.search(r"\[project\].*?dependencies\s*=\s*\[(.*?)\]", content, re.DOTALL)
    if core_match:
        deps["core"] = _parse_dep_list(core_match.group(1))

    # Parse optional dependencies
    for group in ["embeddings", "observability", "dev", "visualization"]:
        pattern = rf"\[project\.optional-dependencies\].*?{group}\s*=\s*\[(.*?)\]"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            deps[group] = _parse_dep_list(match.group(1))

    return deps


def _parse_dep_list(raw: str) -> list[str]:
    """Parse a TOML array of dependency strings."""
    deps = []
    for line in raw.split("\n"):
        line = line.strip().strip(",")
        if line.startswith('"') and line.endswith('"'):
            dep = line.strip('"')
            if dep and not dep.startswith("#"):
                deps.append(dep)
    return deps


def generate_requirements(deps: dict[str, list[str]]) -> str:
    """Generate requirements.txt content from parsed dependencies."""
    lines = [GENERATED_HEADER]

    lines.append("# Core Dependencies (from pyproject.toml [project.dependencies])")
    for dep in sorted(deps["core"], key=str.lower):
        lines.append(dep)
    lines.append("")

    lines.append("# Optional Embeddings (from pyproject.toml [project.optional-dependencies].embeddings)")
    lines.append("# Install with: pip install \".[embeddings]\" when semantic embeddings are needed")
    for dep in sorted(deps["embeddings"], key=str.lower):
        lines.append(dep)
    lines.append("")

    lines.append("# Optional Observability (from pyproject.toml [project.optional-dependencies].observability)")
    lines.append("# Install with: pip install \".[observability]\" for distributed tracing")
    for dep in sorted(deps["observability"], key=str.lower):
        lines.append(dep)
    lines.append("")

    lines.append("# Dev dependencies (from pyproject.toml [project.optional-dependencies].dev)")
    for dep in sorted(deps["dev"], key=str.lower):
        # Skip sentence-transformers as it's already in embeddings
        if "sentence-transformers" not in dep.lower():
            lines.append(dep)
    lines.append("")

    lines.append("# Visualization (optional, from pyproject.toml [project.optional-dependencies].visualization)")
    for dep in sorted(deps["visualization"], key=str.lower):
        # Skip jupyter as it's heavy
        if "jupyter" not in dep.lower():
            lines.append(dep)
    lines.append("")

    lines.append("# Security: Pin minimum versions for indirect dependencies with known vulnerabilities")
    lines.append("certifi>=2025.11.12")
    lines.append("cryptography>=46.0.3")
    lines.append("jinja2>=3.1.6")
    lines.append("urllib3>=2.6.2")
    lines.append("setuptools>=80.9.0")
    lines.append("idna>=3.11")
    lines.append("")

    return "\n".join(lines)


def normalize_requirements(content: str) -> list[str]:
    """Normalize requirements content for comparison.

    Ignores comments, empty lines, and normalizes whitespace.
    Returns sorted list of non-empty, non-comment lines.
    """
    lines = []
    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(line)
    return sorted(lines, key=str.lower)


def main() -> int:
    parser = argparse.ArgumentParser(description="Export requirements.txt from pyproject.toml")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check mode: fail if requirements.txt differs from generated",
    )
    args = parser.parse_args()

    if not PYPROJECT_PATH.exists():
        print(f"ERROR: pyproject.toml not found at {PYPROJECT_PATH}", file=sys.stderr)
        return 1

    pyproject_content = PYPROJECT_PATH.read_text(encoding="utf-8")
    deps = parse_pyproject_deps(pyproject_content)
    generated = generate_requirements(deps)

    if args.check:
        if not REQUIREMENTS_PATH.exists():
            print("ERROR: requirements.txt does not exist", file=sys.stderr)
            return 1

        current = REQUIREMENTS_PATH.read_text(encoding="utf-8")
        current_deps = normalize_requirements(current)
        generated_deps = normalize_requirements(generated)

        if current_deps != generated_deps:
            print("ERROR: Dependency drift detected!", file=sys.stderr)
            print("", file=sys.stderr)
            print("requirements.txt is out of sync with pyproject.toml", file=sys.stderr)
            print("Run: python scripts/ci/export_requirements.py", file=sys.stderr)
            print("", file=sys.stderr)

            current_set = set(current_deps)
            generated_set = set(generated_deps)

            missing = generated_set - current_set
            extra = current_set - generated_set

            if missing:
                print("Missing in requirements.txt:", file=sys.stderr)
                for dep in sorted(missing):
                    print(f"  + {dep}", file=sys.stderr)

            if extra:
                print("Extra in requirements.txt:", file=sys.stderr)
                for dep in sorted(extra):
                    print(f"  - {dep}", file=sys.stderr)

            return 1

        print("✓ requirements.txt is in sync with pyproject.toml")
        return 0

    # Write mode
    REQUIREMENTS_PATH.write_text(generated, encoding="utf-8")
    print(f"✓ Generated {REQUIREMENTS_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
