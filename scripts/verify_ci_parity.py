"""
CI parity guard.

Fails if core CI workflows use raw commands instead of canonical Make targets.
"""

from __future__ import annotations

import pathlib
import re
import sys
from typing import Dict, List, Tuple

import yaml

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

WORKFLOWS = [
    ".github/workflows/ci-neuro-cognitive-engine.yml",
    ".github/workflows/ci-smoke.yml",
]

TARGET_JOBS = {
    "lint",
    "test",
    "coverage",
    "e2e-tests",
    "effectiveness-validation",
    "benchmarks",
    "smoke",
    "coverage-gate",
}

DISALLOWED_PATTERNS: List[Tuple[str, str]] = [
    (r"^\s*ruff\b", "Use `make lint`."),
    (r"^\s*mypy\b", "Use `make type`."),
    (r"^\s*(python -m )?pytest\b", "Use the corresponding Make target (test/e2e/bench/smoke/coverage-gate)."),
    (r"^\s*python\s+scripts/run_effectiveness_suite\.py\b", "Use `make effectiveness`."),
    (r"^\s*\./coverage_gate\.sh\b", "Use `make coverage-gate`."),
]

ALLOWED_PREFIX = re.compile(r"^\s*make\b")


def load_workflow(path: pathlib.Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def check_run_commands(file_path: pathlib.Path, job_id: str, step: Dict, findings: List[Dict]) -> None:
    run = step.get("run")
    if not run:
        return

    for raw_line in run.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ALLOWED_PREFIX.match(line):
            continue
        for pattern, suggestion in DISALLOWED_PATTERNS:
            if re.match(pattern, line):
                findings.append(
                    {
                        "file": str(file_path),
                        "job": job_id,
                        "step": step.get("name", "<unnamed>"),
                        "line": line,
                        "suggestion": suggestion,
                    }
                )
                break


def main() -> int:
    findings: List[Dict] = []

    for workflow in WORKFLOWS:
        path = REPO_ROOT / workflow
        if not path.exists():
            print(f"[WARN] Workflow not found, skipping: {path}")
            continue
        data = load_workflow(path)
        for job_id, job in (data.get("jobs") or {}).items():
            if TARGET_JOBS and job_id not in TARGET_JOBS:
                continue
            for step in job.get("steps", []):
                check_run_commands(path, job_id, step, findings)

    if findings:
        print("❌ CI parity check failed. Replace raw commands with canonical Make targets.\n")
        for item in findings:
            print(
                f"- {item['file']} > job `{item['job']}` > step `{item['step']}`\n"
                f"  Found: `{item['line']}`\n"
                f"  Fix:   {item['suggestion']}\n"
            )
        return 1

    print("✅ CI parity check passed: workflows use canonical Make targets.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
