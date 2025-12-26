from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path  # noqa: TC003

import scripts.readiness.changelog_generator as cg


def test_generate_entry_includes_policy_and_evidence(tmp_path: Path):
    readiness_dir = tmp_path / "docs" / "status"
    readiness_dir.mkdir(parents=True)
    readiness_path = readiness_dir / "READINESS.md"
    readiness_path.write_text("# Title\nLast updated: 2024-01-01\n\n## Change Log\n- old\n", encoding="utf-8")

    def fixed_now():
        return datetime(2024, 2, 2, tzinfo=timezone.utc)

    analysis = {
        "counts": {
            "categories": {"functional_core": 1},
            "risks": {"high": 1},
        },
        "primary_category": "functional_core",
        "max_risk": "high",
    }

    evidence = {"evidence_hash": "sha256-feedface"}
    policy = {"verdict": "approve_with_conditions"}

    _, updated = cg.generate_update(
        "Readiness Update",
        "origin/main",
        root=tmp_path,
        diff_provider=lambda base_ref, root: ["src/mlsdm/core/example.py"],
        analyzer=lambda paths, base_ref, root: analysis,
        evidence_collector=lambda root: evidence,
        policy_evaluator=lambda analysis, evidence: policy,
        now_provider=fixed_now,
    )

    lines = updated.splitlines()
    assert lines[1] == "Last updated: 2024-02-02"
    assert "Evidence hash: sha256-feedface; Policy verdict: approve_with_conditions" in updated
    assert updated.count("Evidence hash") == 1
