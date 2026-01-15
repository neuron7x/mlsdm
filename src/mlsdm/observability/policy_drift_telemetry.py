"""Policy Drift Telemetry for Moral Filter Monitoring.

This module provides Prometheus metrics for detecting and tracking
policy drift in adaptive moral filters. Supports automated alerting
for dangerous threshold changes.

Metrics:
    - moral_threshold_current: Current threshold value per filter
    - moral_threshold_drift_rate: Rate of threshold change per operation
    - moral_threshold_violations: Boundary violations (MIN/MAX)
    - moral_ema_deviation: Deviation from target 0.5
    - moral_drift_events: Total drift events by severity

Usage:
    from mlsdm.observability.policy_drift_telemetry import record_threshold_change

    record_threshold_change(
        filter_id="production",
        old_threshold=0.5,
        new_threshold=0.52,
        ema_value=0.55
    )
"""

import logging
from threading import Lock

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)

# Metrics for policy drift detection
moral_threshold_gauge = Gauge(
    "mlsdm_moral_threshold_current",
    "Current moral filter threshold value",
    ["filter_id"],
)

moral_threshold_drift_rate = Gauge(
    "mlsdm_moral_threshold_drift_rate",
    "Rate of threshold change per operation",
    ["filter_id"],
)

moral_threshold_violations = Counter(
    "mlsdm_moral_threshold_violations_total",
    "Total boundary violations (MIN/MAX)",
    ["filter_id", "boundary"],
)

moral_ema_deviation = Gauge(
    "mlsdm_moral_ema_deviation",
    "Deviation of EMA from target 0.5",
    ["filter_id"],
)

moral_drift_events = Counter(
    "mlsdm_moral_drift_events_total",
    "Total policy drift events detected",
    ["filter_id", "severity"],
)

moral_drift_enforcements = Counter(
    "mlsdm_moral_drift_enforcements_total",
    "Total policy drift enforcement actions executed",
    ["filter_id", "action", "reason"],
)

moral_drift_lockdown_active = Gauge(
    "mlsdm_moral_drift_lockdown_active",
    "Whether the moral filter is in drift lockdown (1=active, 0=inactive)",
    ["filter_id"],
)

_metric_batch: list[dict[str, float | str]] = []
_batch_lock = Lock()
_BATCH_SIZE = 10
_BATCH_DRIFT_THRESHOLD = 0.05


def record_threshold_change(
    filter_id: str, old_threshold: float, new_threshold: float, ema_value: float
) -> None:
    """Record threshold change and calculate drift.

    Args:
        filter_id: Unique identifier for the moral filter
        old_threshold: Previous threshold value
        new_threshold: New threshold value
        ema_value: Current EMA acceptance rate

    Side Effects:
        Updates Prometheus metrics for monitoring and alerting.
        Tracks current threshold, boundary violations, EMA deviation,
        and drift event severity.
    """
    drift = abs(new_threshold - old_threshold)

    if drift < _BATCH_DRIFT_THRESHOLD:
        _enqueue_metric(
            filter_id=filter_id,
            old_threshold=old_threshold,
            new_threshold=new_threshold,
            ema_value=ema_value,
        )
        return

    _record_single_metric(
        filter_id=filter_id,
        old_threshold=old_threshold,
        new_threshold=new_threshold,
        ema_value=ema_value,
    )


def flush_metric_batch() -> None:
    """Flush any batched threshold metrics."""
    with _batch_lock:
        _flush_metrics_locked()


def _enqueue_metric(
    filter_id: str, old_threshold: float, new_threshold: float, ema_value: float
) -> None:
    with _batch_lock:
        _metric_batch.append(
            {
                "filter_id": filter_id,
                "old_threshold": old_threshold,
                "new_threshold": new_threshold,
                "ema_value": ema_value,
            }
        )
        if len(_metric_batch) >= _BATCH_SIZE:
            _flush_metrics_locked()


def _flush_metrics_locked() -> None:
    if not _metric_batch:
        return

    batch = list(_metric_batch)
    _metric_batch.clear()

    for entry in batch:
        _record_single_metric(
            filter_id=str(entry["filter_id"]),
            old_threshold=float(entry["old_threshold"]),
            new_threshold=float(entry["new_threshold"]),
            ema_value=float(entry["ema_value"]),
        )


def _record_single_metric(
    filter_id: str, old_threshold: float, new_threshold: float, ema_value: float
) -> None:
    # Update current value
    moral_threshold_gauge.labels(filter_id=filter_id).set(new_threshold)

    # Calculate drift magnitude
    drift = abs(new_threshold - old_threshold)
    moral_threshold_drift_rate.labels(filter_id=filter_id).set(drift)

    # Check for boundary violations
    if new_threshold <= 0.30:
        moral_threshold_violations.labels(filter_id=filter_id, boundary="MIN").inc()
    elif new_threshold >= 0.90:
        moral_threshold_violations.labels(filter_id=filter_id, boundary="MAX").inc()

    # EMA deviation from healthy 0.5
    deviation = abs(ema_value - 0.5)
    moral_ema_deviation.labels(filter_id=filter_id).set(deviation)

    # Detect drift severity (using absolute threshold differences)
    if drift > 0.1:  # CRITICAL: >0.1 absolute change
        moral_drift_events.labels(filter_id=filter_id, severity="critical").inc()
    elif drift > 0.05:  # WARNING: >0.05 absolute change
        moral_drift_events.labels(filter_id=filter_id, severity="warning").inc()


def record_drift_enforcement(
    filter_id: str,
    action: str,
    reason: str,
    drift_magnitude: float,
    lockdown_active: bool,
) -> None:
    """Record enforcement actions for policy drift."""
    moral_drift_enforcements.labels(filter_id=filter_id, action=action, reason=reason).inc()
    moral_drift_lockdown_active.labels(filter_id=filter_id).set(1.0 if lockdown_active else 0.0)
    logger.error(
        "Policy drift enforcement recorded: filter=%s action=%s reason=%s drift=%.3f",
        filter_id,
        action,
        reason,
        drift_magnitude,
    )
