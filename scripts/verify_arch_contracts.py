"""Verify architectural contracts for canonical defaults and documentation consistency."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from mlsdm.config.calibration import RATE_LIMIT_DEFAULTS
from mlsdm.config.defaults import (
    DEFAULT_CONFIG_PATH,
    RATE_LIMIT_REQUESTS_DEFAULT,
    RATE_LIMIT_WINDOW_DEFAULT,
)
from mlsdm.config.runtime import RuntimeMode, get_runtime_config


def _require_sections(path: Path, sections: list[str], errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"Missing required doc: {path}")
        return
    content = path.read_text(encoding="utf-8")
    for section in sections:
        if section not in content:
            errors.append(f"Missing section '{section}' in {path}")


def main() -> int:
    repo_root = PROJECT_ROOT
    errors: list[str] = []

    _require_sections(
        repo_root / "docs" / "ARCHITECTURE_MAP.md",
        ["Architecture Type", "System Map Summary"],
        errors,
    )
    _require_sections(
        repo_root / "docs" / "ARCH_CONTRACTS.md",
        ["Module Contracts", "Contract Ledger"],
        errors,
    )

    allowed_default_hits = {
        Path("src/mlsdm/config/defaults.py"),
        Path("src/mlsdm/entrypoints/dev_entry.py"),
    }
    default_hits = []
    for path in (repo_root / "src").rglob("*.py"):
        if DEFAULT_CONFIG_PATH in path.read_text(encoding="utf-8"):
            default_hits.append(path.relative_to(repo_root))
    unexpected_hits = set(default_hits) - allowed_default_hits
    if unexpected_hits:
        errors.append(
            "Unexpected default config path references: "
            + ", ".join(str(path) for path in sorted(unexpected_hits))
        )

    if RATE_LIMIT_DEFAULTS.requests_per_window != RATE_LIMIT_REQUESTS_DEFAULT:
        errors.append("RATE_LIMIT_DEFAULTS.requests_per_window does not match canonical default")
    if RATE_LIMIT_DEFAULTS.window_seconds != RATE_LIMIT_WINDOW_DEFAULT:
        errors.append("RATE_LIMIT_DEFAULTS.window_seconds does not match canonical default")

    runtime_defaults = get_runtime_config(mode=RuntimeMode.DEV)
    if runtime_defaults.security.rate_limit_requests != RATE_LIMIT_REQUESTS_DEFAULT:
        errors.append("RuntimeConfig rate_limit_requests does not match canonical default")
    if runtime_defaults.security.rate_limit_window != RATE_LIMIT_WINDOW_DEFAULT:
        errors.append("RuntimeConfig rate_limit_window does not match canonical default")

    security_policy = (repo_root / "docs" / "SECURITY_POLICY.md").read_text(encoding="utf-8")
    requests_match = re.search(r"RATE_LIMIT_REQUESTS.*default: (\d+)", security_policy)
    window_match = re.search(r"RATE_LIMIT_WINDOW.*default: (\d+)", security_policy)
    if requests_match and int(requests_match.group(1)) != RATE_LIMIT_REQUESTS_DEFAULT:
        errors.append("SECURITY_POLICY.md default RATE_LIMIT_REQUESTS is out of sync")
    if window_match and int(window_match.group(1)) != RATE_LIMIT_WINDOW_DEFAULT:
        errors.append("SECURITY_POLICY.md default RATE_LIMIT_WINDOW is out of sync")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Architecture contracts verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
