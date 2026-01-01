#!/usr/bin/env python3
"""Capture reproducible evidence snapshot (coverage + JUnit logs only).

Writes artifacts to: artifacts/evidence/YYYY-MM-DD/<short_sha>/
Required outputs:
  - coverage/coverage.xml
  - pytest/junit.xml
  - logs/*.log
  - manifest.json (schema_version: evidence-v1)
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

SCHEMA_VERSION = "evidence-v1"


class CaptureError(Exception):
    """Raised when evidence capture fails."""


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def git_sha() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def _prefer_uv(command: List[str]) -> List[str]:
    """Prefix command with `uv run` if available to mirror CI."""
    if shutil.which("uv"):
        return ["uv", "run", *command]
    return command


def run_command(command: List[str], log_path: Path) -> subprocess.CompletedProcess[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        command,
        cwd=repo_root(),
        capture_output=True,
        text=True,
        check=False,
    )
    log_path.write_text(
        "COMMAND: "
        + " ".join(command)
        + "\n\nSTDOUT:\n"
        + result.stdout
        + "\nSTDERR:\n"
        + result.stderr
        + f"\nEXIT CODE: {result.returncode}\n",
        encoding="utf-8",
    )
    return result


def capture_coverage(evidence_dir: Path, commands: list[str], produced: list[Path]) -> None:
    coverage_xml = repo_root() / "coverage.xml"
    if coverage_xml.exists():
        coverage_xml.unlink()

    log_path = evidence_dir / "logs" / "coverage_gate.log"
    command = _prefer_uv(["bash", "./coverage_gate.sh"])
    commands.append(" ".join(command))
    result = run_command(command, log_path)

    src = repo_root() / "coverage.xml"
    dest_dir = evidence_dir / "coverage"
    dest_dir.mkdir(parents=True, exist_ok=True)
    if not src.exists():
        raise CaptureError("coverage.xml not produced by coverage gate")
    shutil.copy(src, dest_dir / "coverage.xml")
    produced.append(dest_dir / "coverage.xml")
    produced.append(log_path)

    if result.returncode != 0:
        raise CaptureError(
            f"coverage gate failed; see {log_path.relative_to(evidence_dir)}"
        )


def capture_pytest_junit(
    evidence_dir: Path, commands: list[str], produced: list[Path]
) -> None:
    reports_dir = repo_root() / "reports"
    reports_dir.mkdir(exist_ok=True)
    junit_path = reports_dir / "junit-unit.xml"
    if junit_path.exists():
        junit_path.unlink()

    log_path = evidence_dir / "logs" / "unit_tests.log"
    command = _prefer_uv(
        [
            "python",
            "-m",
            "pytest",
            "tests/unit",
            "-q",
            "--junitxml",
            str(junit_path),
            "--maxfail=1",
        ]
    )
    commands.append(" ".join(command))
    result = run_command(command, log_path)

    dest_dir = evidence_dir / "pytest"
    dest_dir.mkdir(parents=True, exist_ok=True)
    if not junit_path.exists():
        raise CaptureError("junit.xml not produced by pytest run")
    shutil.copy(junit_path, dest_dir / "junit.xml")
    produced.append(dest_dir / "junit.xml")
    produced.append(log_path)

    if result.returncode != 0:
        raise CaptureError(f"unit tests failed; see {log_path.relative_to(evidence_dir)}")


def write_manifest(
    evidence_dir: Path, commands: Iterable[str], produced: Iterable[Path], sha: str
) -> None:
    produced_paths = {path for path in produced if path.exists()}
    produced_paths.add(evidence_dir / "manifest.json")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "git_sha": sha,
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "python_version": sys.version.split()[0],
        "commands": list(commands),
        "produced_files": sorted(
            {str(path.relative_to(evidence_dir)) for path in produced_paths}
        ),
    }
    (evidence_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> int:
    root = repo_root()
    os.chdir(root)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    sha_full = git_sha()
    short_sha = sha_full[:12] if sha_full != "unknown" else "unknown"
    base_dir = root / "artifacts" / "evidence"
    base_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path(tempfile.mkdtemp(prefix="evidence-", dir=base_dir))
    evidence_dir = temp_dir

    commands: list[str] = []
    produced: list[Path] = []

    try:
        capture_coverage(evidence_dir, commands, produced)
        capture_pytest_junit(evidence_dir, commands, produced)
        write_manifest(evidence_dir, commands, produced, sha_full)
    except CaptureError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print(f"Logs preserved at {temp_dir}", file=sys.stderr)
        return 1

    final_parent = root / "artifacts" / "evidence" / date_str
    final_parent.mkdir(parents=True, exist_ok=True)
    final_dir = final_parent / short_sha
    if final_dir.exists():
        shutil.rmtree(final_dir)
    shutil.move(str(temp_dir), final_dir)

    print(f"Evidence captured at {final_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
