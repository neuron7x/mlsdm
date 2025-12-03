#!/usr/bin/env python3
"""Generate Software Bill of Materials (SBOM) for MLSDM.

This script generates an SBOM in CycloneDX JSON format, which can be used
for supply chain security analysis, vulnerability scanning, and compliance.

Usage:
    python scripts/generate_sbom.py [--output FILE] [--format FORMAT]

Requirements:
    pip install cyclonedx-bom

Example:
    # Generate default SBOM
    python scripts/generate_sbom.py

    # Generate SBOM in specific format
    python scripts/generate_sbom.py --output sbom.json --format json
    python scripts/generate_sbom.py --output sbom.xml --format xml
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_project_version() -> str:
    """Get project version from pyproject.toml or setup.py."""
    try:
        import tomllib
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                return data.get("project", {}).get("version", "0.0.0")
    except Exception:
        pass
    return "0.0.0"


def run_cyclonedx_bom(output_path: str, output_format: str = "json") -> bool:
    """Run cyclonedx-bom to generate SBOM.

    Args:
        output_path: Path to output file
        output_format: Output format (json or xml)

    Returns:
        True if successful, False otherwise
    """
    cmd = [
        sys.executable, "-m", "cyclonedx_py",
        "environment",
        "--output", output_path,
        "--format", output_format,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"SBOM generated successfully: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error generating SBOM: {e.stderr}")
        return False
    except FileNotFoundError:
        print("cyclonedx-bom not installed. Install with: pip install cyclonedx-bom")
        return False


def generate_simple_sbom(output_path: str) -> bool:
    """Generate a simple SBOM from requirements.txt as fallback.

    Args:
        output_path: Path to output file

    Returns:
        True if successful, False otherwise
    """
    requirements_path = Path(__file__).parent.parent / "requirements.txt"

    if not requirements_path.exists():
        print(f"requirements.txt not found at {requirements_path}")
        return False

    components = []

    with open(requirements_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Parse requirement line
            name = ""
            version = "*"

            if ">=" in line:
                parts = line.split(">=")
                name = parts[0].strip()
                version = parts[1].split(",")[0].strip() if len(parts) > 1 else "*"
            elif "==" in line:
                parts = line.split("==")
                name = parts[0].strip()
                version = parts[1].strip() if len(parts) > 1 else "*"
            elif "~=" in line:
                parts = line.split("~=")
                name = parts[0].strip()
                version = parts[1].strip() if len(parts) > 1 else "*"
            else:
                name = line.split("[")[0].strip()

            if name:
                components.append({
                    "type": "library",
                    "name": name,
                    "version": version,
                    "purl": f"pkg:pypi/{name.lower()}@{version}",
                })

    sbom = {
        "$schema": "http://cyclonedx.org/schema/bom-1.5.schema.json",
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:mlsdm-sbom-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tools": [
                {
                    "vendor": "MLSDM",
                    "name": "generate_sbom.py",
                    "version": "1.0.0",
                }
            ],
            "component": {
                "type": "application",
                "name": "mlsdm-governed-cognitive-memory",
                "version": get_project_version(),
                "description": "Governed Cognitive Memory for LLM Safety",
            },
        },
        "components": components,
    }

    with open(output_path, "w") as f:
        json.dump(sbom, f, indent=2)

    print(f"Simple SBOM generated: {output_path}")
    print(f"  Components: {len(components)}")
    return True


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate SBOM for MLSDM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        "-o",
        default="sbom.json",
        help="Output file path (default: sbom.json)",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=["json", "xml"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--simple",
        action="store_true",
        help="Use simple parser (no cyclonedx-bom required)",
    )

    args = parser.parse_args()

    print(f"Generating SBOM for MLSDM v{get_project_version()}...")

    if args.simple:
        success = generate_simple_sbom(args.output)
    else:
        # Try cyclonedx-bom first, fall back to simple parser
        success = run_cyclonedx_bom(args.output, args.format)
        if not success:
            print("Falling back to simple SBOM generator...")
            success = generate_simple_sbom(args.output)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
