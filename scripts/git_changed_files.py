from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Iterable


def repo_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent
    return current.parent.parent


def _ref_exists(ref: str, root: Path) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", ref],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _diff_names(root: Path, ref: str) -> list[str]:
    try:
        diff = subprocess.check_output(
            [
                "git",
                "diff",
                "--name-only",
                "--diff-filter=ACMRTUXB",
                f"{ref}...HEAD",
            ],
            cwd=root,
            text=True,
        )
    except subprocess.CalledProcessError:
        diff = ""
    return [line for line in diff.splitlines() if line.strip()]


def _fallback_names(root: Path) -> list[str]:
    try:
        fallback = subprocess.check_output(
            [
                "git",
                "show",
                "--pretty=format:",
                "--name-only",
                "--diff-filter=ACMRTUXB",
                "HEAD",
            ],
            cwd=root,
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [line for line in fallback.splitlines() if line.strip()]


def list_changed_files(ref_log: list[str] | None = None) -> list[str]:
    root = repo_root()
    refs_checked = ref_log if ref_log is not None else []
    base_ref = os.environ.get("GITHUB_BASE_REF")
    candidates = []
    if base_ref:
        candidates.append(f"origin/{base_ref}")
    candidates.extend(["origin/main", "HEAD~1"])

    for ref in candidates:
        if not _ref_exists(ref, root):
            refs_checked.append(f"{ref} (missing)")
            continue
        refs_checked.append(ref)
        files = _diff_names(root, ref)
        if files:
            return files

    refs_checked.append("HEAD (show)")
    return _fallback_names(root)
