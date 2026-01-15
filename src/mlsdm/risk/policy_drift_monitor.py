from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import IntEnum
from functools import lru_cache

from mlsdm.observability.policy_drift_telemetry import (
    record_policy_drift_state_change,
)
from mlsdm.policy.loader import DEFAULT_POLICY_DIR, PolicyLoadError, load_policy_bundle

logger = logging.getLogger(__name__)


class PolicyDriftState(IntEnum):
    OK = 0
    WARN = 1
    DEGRADED = 2
    HALT = 3


@dataclass(frozen=True)
class DriftBudget:
    max_drift: float
    warn_at: float
    degraded_at: float
    min_threshold: float
    max_threshold: float


@dataclass(frozen=True)
class PolicyDriftDecision:
    state: PolicyDriftState
    drift: float
    budget: float
    ratio: float
    action: str
    clamped_threshold: float | None


@lru_cache(maxsize=1)
def _load_drift_budget() -> DriftBudget:
    try:
        bundle = load_policy_bundle(DEFAULT_POLICY_DIR)
    except PolicyLoadError as exc:
        raise RuntimeError(f"Failed to load policy drift budget: {exc}") from exc

    for component in bundle.observability_slo.thresholds.slos.cognitive_engine:
        if component.name == "moral-filter-stability":
            targets = component.targets
            if targets.threshold_drift_max is None:
                raise RuntimeError("Policy drift budget missing threshold_drift_max")
            if targets.min_threshold is None or targets.max_threshold is None:
                raise RuntimeError("Policy drift budget missing min/max thresholds")

            max_drift = float(targets.threshold_drift_max)
            warn_at = max_drift * 0.5
            degraded_at = max_drift * 0.8
            return DriftBudget(
                max_drift=max_drift,
                warn_at=warn_at,
                degraded_at=degraded_at,
                min_threshold=float(targets.min_threshold),
                max_threshold=float(targets.max_threshold),
            )

    raise RuntimeError("Policy drift budget missing moral-filter-stability targets")


class PolicyDriftMonitor:
    def __init__(self, baseline_threshold: float, filter_id: str) -> None:
        self._baseline_threshold = float(baseline_threshold)
        self._filter_id = filter_id
        self._budget = _load_drift_budget()
        self.state = PolicyDriftState.OK
        self.halted = False

    @property
    def budget(self) -> DriftBudget:
        return self._budget

    def evaluate(self, new_threshold: float, ema_value: float) -> PolicyDriftDecision:
        drift = abs(float(new_threshold) - self._baseline_threshold)
        next_state = self._classify_state(drift)
        action = "none"
        clamped_threshold = None

        if next_state > self.state:
            previous = self.state
            self.state = next_state
            record_policy_drift_state_change(
                filter_id=self._filter_id,
                state=self.state,
                drift=drift,
                budget=self._budget.max_drift,
                ema_value=ema_value,
            )
            if next_state == PolicyDriftState.HALT:
                self.halted = True
                action = "clamp"
                clamped_threshold = self._clamp_threshold(self._baseline_threshold)
                logger.error(
                    "Policy drift HALT for filter '%s': drift=%.3f budget=%.3f (state=%s)",
                    self._filter_id,
                    drift,
                    self._budget.max_drift,
                    self.state.name,
                )
            else:
                logger.warning(
                    "Policy drift escalation for filter '%s': %s → %s (drift=%.3f budget=%.3f)",
                    self._filter_id,
                    previous.name,
                    self.state.name,
                    drift,
                    self._budget.max_drift,
                )

        if self.halted:
            action = "clamp"
            clamped_threshold = self._clamp_threshold(self._baseline_threshold)

        ratio = drift / self._budget.max_drift if self._budget.max_drift else 0.0
        return PolicyDriftDecision(
            state=self.state,
            drift=drift,
            budget=self._budget.max_drift,
            ratio=ratio,
            action=action,
            clamped_threshold=clamped_threshold,
        )

    def _classify_state(self, drift: float) -> PolicyDriftState:
        if drift > self._budget.max_drift:
            return PolicyDriftState.HALT
        if drift > self._budget.degraded_at:
            return PolicyDriftState.DEGRADED
        if drift > self._budget.warn_at:
            return PolicyDriftState.WARN
        return PolicyDriftState.OK

    def _clamp_threshold(self, threshold: float) -> float:
        return min(self._budget.max_threshold, max(self._budget.min_threshold, threshold))
