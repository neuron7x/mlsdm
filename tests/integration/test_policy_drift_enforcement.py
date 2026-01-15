from __future__ import annotations

import json
from pathlib import Path

import pytest

from mlsdm.cognition.moral_filter_v2 import MoralFilterV2
from mlsdm.risk.policy_drift_monitor import PolicyDriftState


def test_policy_drift_halt_clamps_threshold() -> None:
    moral = MoralFilterV2(initial_threshold=0.5, filter_id="policy-drift-e2e")
    moral.ema_accept_rate = 1.0

    for _ in range(10):
        moral.adapt(True)
        if moral._halted:
            break

    assert moral._halted is True
    assert moral._drift_monitor.state == PolicyDriftState.HALT
    assert moral.threshold == pytest.approx(0.5)

    evidence = {
        "filter_id": "policy-drift-e2e",
        "state": moral._drift_monitor.state.name,
        "halted": moral._halted,
        "threshold": moral.threshold,
        "budget": moral._drift_monitor.budget.max_drift,
    }
    evidence_dir = Path("artifacts") / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "policy_drift_report.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
