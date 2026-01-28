from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.validation
def test_quality_index_exists() -> None:
    quality_index = REPO_ROOT / "docs" / "QUALITY_INDEX.md"
    assert quality_index.is_file(), "docs/QUALITY_INDEX.md must exist"
    assert quality_index.read_text(encoding="utf-8").strip(), "QUALITY_INDEX.md empty"


@pytest.mark.validation
def test_mutation_baseline_schema_and_invariant() -> None:
    mutation_baseline = REPO_ROOT / "quality" / "mutation_baseline.json"
    assert mutation_baseline.is_file(), "quality/mutation_baseline.json must exist"
    payload = json.loads(mutation_baseline.read_text(encoding="utf-8"))

    required_keys = {
        "total_mutants",
        "killed",
        "survived",
        "timeout",
        "skipped",
        "score",
        "status",
    }
    assert required_keys.issubset(payload.keys())

    total_mutants = payload["total_mutants"]
    score = payload["score"]
    status = payload["status"]

    assert isinstance(total_mutants, int)
    assert isinstance(score, (int, float))
    assert isinstance(status, str)

    if total_mutants == 0:
        assert status == "needs_regeneration"
        assert score == 0.0
