from __future__ import annotations

import json
from pathlib import Path

from scripts.export_openapi import export_openapi
from scripts.openapi_contract_check import check_breaking_changes


def test_openapi_contract_check_writes_evidence() -> None:
    evidence_dir = Path("artifacts") / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    candidate_path = evidence_dir / "openapi_schema.json"
    baseline_path = Path("docs") / "openapi-baseline.json"

    assert export_openapi(output_path=str(candidate_path), validate=False) is True

    baseline_spec = json.loads(baseline_path.read_text(encoding="utf-8"))
    candidate_spec = json.loads(candidate_path.read_text(encoding="utf-8"))
    failures = check_breaking_changes(baseline_spec, candidate_spec)

    report = {
        "baseline": str(baseline_path),
        "candidate": str(candidate_path),
        "breaking_changes": failures,
        "status": "pass" if not failures else "fail",
    }
    (evidence_dir / "openapi_diff_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )

    assert failures == []
