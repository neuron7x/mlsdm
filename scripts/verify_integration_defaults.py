#!/usr/bin/env python3
"""Verify canonical defaults are not duplicated across runtime modules."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _scan_for_literal(root: Path, literal: str, exclude: set[Path]) -> list[Path]:
    matches: list[Path] = []
    for path in root.rglob("*.py"):
        if path in exclude:
            continue
        text = path.read_text(encoding="utf-8")
        if literal in text:
            matches.append(path)
    return matches


def main() -> int:
    from mlsdm.config.defaults import DEFAULT_CONFIG_PATH, PRODUCTION_CONFIG_PATH

    src_root = PROJECT_ROOT / "src" / "mlsdm"
    exclude = {
        src_root / "config" / "defaults.py",
    }

    violations: list[str] = []
    for literal in (DEFAULT_CONFIG_PATH, PRODUCTION_CONFIG_PATH):
        matches = _scan_for_literal(src_root, literal, exclude)
        for path in matches:
            violations.append(f"{path.relative_to(PROJECT_ROOT)}: {literal}")

    if violations:
        print("ERROR: Duplicate canonical defaults detected:", file=sys.stderr)
        for entry in violations:
            print(f" - {entry}", file=sys.stderr)
        return 1

    print("✓ Canonical defaults verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
