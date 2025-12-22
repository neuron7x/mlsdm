#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional

ROOT = Path(__file__).resolve().parent.parent
READINESS_PATH = ROOT / "docs" / "status" / "READINESS.md"
MAX_AGE_DAYS = 14
LAST_UPDATED_PATTERN = r"Last updated:\s*(\d{4}-\d{2}-\d{2})"


def log_error(message: str) -> None:
    print(f"::error::{message}")


def ensure_readiness_file() -> bool:
    if READINESS_PATH.exists():
        return True
    log_error(f"Missing readiness file: {READINESS_PATH}")
    return False


def parse_last_updated() -> Optional[datetime]:
    content = READINESS_PATH.read_text(encoding="utf-8")
    match = re.search(LAST_UPDATED_PATTERN, content)
    if not match:
        log_error("Last updated date not found in docs/status/READINESS.md")
        return None
    try:
        return datetime.strptime(match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        log_error("Last updated date is not in YYYY-MM-DD format")
        return None


def last_updated_is_fresh(last_updated: datetime) -> bool:
    age_days = (datetime.now(timezone.utc) - last_updated).days
    if age_days > MAX_AGE_DAYS:
        log_error(
            f"docs/status/READINESS.md is {age_days} days old (limit: {MAX_AGE_DAYS}). "
            "Update the Last updated field with current evidence."
        )
        return False
    return True


def run_git_diff(ref: str) -> tuple[List[str], bool]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{ref}..HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log_error(f"git diff failed for {ref}: {result.stderr.strip()}")
        return [], False
    return [line.strip() for line in result.stdout.splitlines() if line.strip()], True


def working_tree_diff() -> tuple[List[str], bool]:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        log_error(f"git diff failed for working tree: {result.stderr.strip()}")
        return [], False
    return [line.strip() for line in result.stdout.splitlines() if line.strip()], True


def ref_exists(ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def collect_changed_files() -> List[str]:
    had_git_errors = False
    refs_to_try: List[str] = []
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref:
        refs_to_try.append(f"origin/{base_ref}")
    refs_to_try.extend(["origin/main", "main"])

    for candidate in refs_to_try:
        if ref_exists(candidate):
            diff, ok = run_git_diff(candidate)
            had_git_errors = had_git_errors or not ok
            if diff:
                return diff

    if ref_exists("HEAD^"):
        diff, ok = run_git_diff("HEAD^")
        had_git_errors = had_git_errors or not ok
        if diff:
            return diff

    diff, ok = working_tree_diff()
    had_git_errors = had_git_errors or not ok

    if had_git_errors and not diff:
        log_error("Unable to determine changed files due to git errors.")
        return []

    return diff


def is_scoped(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.startswith(("src/", "tests/", "config/", "configs/", ".github/workflows/")):
        return True
    if Path(normalized).name.startswith("Dockerfile"):
        return True
    return False


def readiness_updated(changed_files: Iterable[str]) -> bool:
    return any(Path(f).as_posix() == "docs/status/READINESS.md" for f in changed_files)


def main() -> int:
    if not ensure_readiness_file():
        return 1

    last_updated = parse_last_updated()
    if last_updated is None or not last_updated_is_fresh(last_updated):
        return 1

    changed_files = collect_changed_files()
    scoped_changes = [f for f in changed_files if is_scoped(f)]

    if scoped_changes and not readiness_updated(changed_files):
        scoped_list = ", ".join(scoped_changes[:10])
        if len(scoped_changes) > 10:
            scoped_list += f", ... (+{len(scoped_changes) - 10} more)"
        log_error(
            "Code/test/config/workflow changes detected without updating docs/status/READINESS.md. "
            f"Touched files: {scoped_list}"
        )
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
