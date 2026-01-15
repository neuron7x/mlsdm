from __future__ import annotations

from mlsdm.risk.policy_drift_monitor import PolicyDriftMonitor, PolicyDriftState


def test_policy_drift_monitor_escalates_and_halts() -> None:
    monitor = PolicyDriftMonitor(baseline_threshold=0.5, filter_id="unit-test")

    decision_warn = monitor.evaluate(0.58, ema_value=0.6)
    assert decision_warn.state == PolicyDriftState.WARN

    decision_degraded = monitor.evaluate(0.63, ema_value=0.6)
    assert decision_degraded.state == PolicyDriftState.DEGRADED

    decision_halt = monitor.evaluate(0.7, ema_value=0.6)
    assert decision_halt.state == PolicyDriftState.HALT
    assert decision_halt.action == "clamp"

    decision_after = monitor.evaluate(0.55, ema_value=0.6)
    assert decision_after.state == PolicyDriftState.HALT
