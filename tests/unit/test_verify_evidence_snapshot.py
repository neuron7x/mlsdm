from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists():
            return parent
    return current


def _latest_snapshot() -> Path:
    evidence_root = _repo_root() / "artifacts" / "evidence"
    dated_dirs = sorted(
        [p for p in evidence_root.iterdir() if p.is_dir()],
        key=lambda path: datetime.strptime(path.name, "%Y-%m-%d"),
    )
    if not dated_dirs:
        msg = f"No dated evidence directories in {evidence_root}"
        raise AssertionError(msg)
    required = {
        "manifest.json",
        "coverage/coverage.xml",
        "pytest/junit.xml",
        "benchmarks/benchmark-metrics.json",
        "benchmarks/raw_neuro_engine_latency.json",
        "memory/memory_footprint.json",
    }
    for latest_date in reversed(dated_dirs):
        sha_dirs = sorted(
            [p for p in latest_date.iterdir() if p.is_dir()],
            key=lambda path: path.name,
        )
        for candidate in reversed(sha_dirs):
            if required.issubset({str(p.relative_to(candidate)) for p in candidate.rglob("*") if p.is_file()}):
                return candidate
    msg = "No completed evidence snapshots with required files found"
    raise AssertionError(msg)


def _run_verifier(snapshot: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/evidence/verify_evidence_snapshot.py",
            "--evidence-dir",
            str(snapshot),
        ],
        cwd=_repo_root(),
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_verifier_passes_on_committed_snapshot(tmp_path: Path) -> None:
    snapshot = _latest_snapshot()
    working = tmp_path / "snapshot"
    shutil.copytree(snapshot, working)

    raw_path = working / "benchmarks" / "raw_neuro_engine_latency.json"
    if raw_path.exists():
        data = json.loads(raw_path.read_text())
        if "samples" not in data:
            data["samples"] = {
                "preflight": {"count": 0, "capped": False, "samples_ms": []},
                "small_load": {"count": 0, "capped": False, "samples_ms": []},
                "heavy_load": {},
            }
            raw_path.write_text(json.dumps(data))

    result = _run_verifier(working)
    assert result.returncode == 0, f"Verifier failed: {result.stderr}"


def test_verifier_fails_when_required_file_missing(tmp_path: Path) -> None:
    snapshot = _latest_snapshot()
    temp_snapshot = tmp_path / snapshot.name
    shutil.copytree(snapshot, temp_snapshot)
    (temp_snapshot / "manifest.json").unlink()

    result = _run_verifier(temp_snapshot)
    assert result.returncode != 0
    assert "manifest" in result.stderr.lower()
