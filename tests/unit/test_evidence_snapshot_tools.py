from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.evidence.verify_evidence_snapshot import EvidenceError, SCHEMA_VERSION, verify_snapshot


def _build_snapshot(tmp_path: Path) -> Path:
    evidence_dir = tmp_path / "artifacts" / "evidence" / "2026-01-01" / "abcdef123456"
    (evidence_dir / "coverage").mkdir(parents=True, exist_ok=True)
    (evidence_dir / "pytest").mkdir(parents=True, exist_ok=True)
    (evidence_dir / "logs").mkdir(parents=True, exist_ok=True)

    (evidence_dir / "coverage" / "coverage.xml").write_text(
        '<coverage line-rate="0.80" branch-rate="0.0"></coverage>', encoding="utf-8"
    )
    (evidence_dir / "pytest" / "junit.xml").write_text(
        '<testsuite name="unit" tests="2" failures="0" errors="0" skipped="0"></testsuite>',
        encoding="utf-8",
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "git_sha": "abcdef1234567890",
        "date_utc": "2026-01-01",
        "python_version": "3.11.0",
        "commands": ["uv run bash ./coverage_gate.sh", "uv run python -m pytest tests/unit -q --junitxml=..."],
        "produced_files": [
            "coverage/coverage.xml",
            "pytest/junit.xml",
            "logs/coverage_gate.log",
        ],
    }
    (evidence_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (evidence_dir / "logs" / "coverage_gate.log").write_text("ok", encoding="utf-8")
    return evidence_dir


def test_verify_snapshot_passes_for_minimal_valid_snapshot(tmp_path: Path) -> None:
    snapshot = _build_snapshot(tmp_path)
    verify_snapshot(snapshot)


def test_verify_snapshot_fails_when_coverage_missing(tmp_path: Path) -> None:
    snapshot = _build_snapshot(tmp_path)
    (snapshot / "coverage" / "coverage.xml").unlink()
    with pytest.raises(EvidenceError):
        verify_snapshot(snapshot)
