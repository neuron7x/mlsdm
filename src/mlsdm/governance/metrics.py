"""
Governance Metrics for MLSDM.

This module provides Prometheus-compatible metrics for tracking governance
decisions, mode transitions, and rule evaluations.

Metrics:
- mlsdm_governance_decisions_total: Counter by action, mode, rule_id
- mlsdm_governance_blocked_total: Counter of blocked requests
- mlsdm_governance_modified_total: Counter of modified responses
- mlsdm_governance_escalated_total: Counter of escalated requests
- mlsdm_governance_mode: Gauge for current operating mode

Usage:
    from mlsdm.governance.metrics import (
        record_governance_decision,
        set_governance_mode,
        get_governance_metrics,
    )

    record_governance_decision(decision)
    set_governance_mode("cautious")
"""

from __future__ import annotations

import logging
from threading import Lock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mlsdm.governance.enforcer import GovernanceDecision

_logger = logging.getLogger(__name__)


class GovernanceMetrics:
    """
    Thread-safe metrics collector for governance events.

    Provides counters and gauges for monitoring governance decisions
    without requiring Prometheus client library (optional integration).
    """

    # Mode numeric mapping for gauge
    MODE_VALUES: dict[str, float] = {
        "normal": 0.0,
        "cautious": 1.0,
        "emergency": 2.0,
    }

    def __init__(self) -> None:
        """Initialize metrics with zero values."""
        self._lock = Lock()

        # Counters
        self._total_decisions = 0
        self._decisions_by_action: dict[str, int] = {}
        self._decisions_by_mode: dict[str, int] = {}
        self._decisions_by_rule: dict[str, int] = {}

        # Action-specific counters
        self._blocked_total = 0
        self._modified_total = 0
        self._escalated_total = 0
        self._allowed_total = 0

        # Mode-specific blocked counters
        self._blocked_by_mode: dict[str, int] = {}

        # Current mode gauge
        self._current_mode = "normal"
        self._current_mode_value = 0.0

        # Mode transition counter
        self._mode_transitions = 0
        self._mode_transition_history: list[tuple[str, str]] = []

    def record_decision(self, decision: GovernanceDecision) -> None:
        """
        Record a governance decision.

        Args:
            decision: The GovernanceDecision to record
        """
        with self._lock:
            self._total_decisions += 1

            # Record by action
            action = decision.action
            self._decisions_by_action[action] = (
                self._decisions_by_action.get(action, 0) + 1
            )

            # Record by mode
            mode = decision.mode
            self._decisions_by_mode[mode] = (
                self._decisions_by_mode.get(mode, 0) + 1
            )

            # Record by rule
            rule_id = decision.rule_id or "default"
            self._decisions_by_rule[rule_id] = (
                self._decisions_by_rule.get(rule_id, 0) + 1
            )

            # Update action-specific counters
            if action == "block":
                self._blocked_total += 1
                self._blocked_by_mode[mode] = (
                    self._blocked_by_mode.get(mode, 0) + 1
                )
            elif action == "modify":
                self._modified_total += 1
            elif action == "escalate":
                self._escalated_total += 1
            elif action == "allow":
                self._allowed_total += 1

    def set_mode(self, mode: str) -> None:
        """
        Set the current operating mode.

        Args:
            mode: Mode name ("normal", "cautious", "emergency")
        """
        with self._lock:
            if mode != self._current_mode:
                old_mode = self._current_mode
                self._mode_transitions += 1
                self._mode_transition_history.append((old_mode, mode))

                # Keep only last 100 transitions
                if len(self._mode_transition_history) > 100:
                    self._mode_transition_history = self._mode_transition_history[-100:]

            self._current_mode = mode
            self._current_mode_value = self.MODE_VALUES.get(mode, 0.0)

    def get_snapshot(self) -> dict[str, Any]:
        """
        Get current snapshot of all metrics.

        Returns:
            Dictionary with all metric values
        """
        with self._lock:
            return {
                "total_decisions": self._total_decisions,
                "decisions_by_action": dict(self._decisions_by_action),
                "decisions_by_mode": dict(self._decisions_by_mode),
                "decisions_by_rule": dict(self._decisions_by_rule),
                "blocked_total": self._blocked_total,
                "modified_total": self._modified_total,
                "escalated_total": self._escalated_total,
                "allowed_total": self._allowed_total,
                "blocked_by_mode": dict(self._blocked_by_mode),
                "current_mode": self._current_mode,
                "current_mode_value": self._current_mode_value,
                "mode_transitions": self._mode_transitions,
            }

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary statistics.

        Returns:
            Dictionary with summary statistics
        """
        with self._lock:
            total = self._total_decisions or 1  # Avoid division by zero

            return {
                "total_decisions": self._total_decisions,
                "block_rate": round(self._blocked_total / total, 4),
                "modify_rate": round(self._modified_total / total, 4),
                "escalate_rate": round(self._escalated_total / total, 4),
                "allow_rate": round(self._allowed_total / total, 4),
                "current_mode": self._current_mode,
                "mode_transitions": self._mode_transitions,
                "top_rules": self._get_top_rules(5),
            }

    def _get_top_rules(self, n: int) -> list[tuple[str, int]]:
        """Get top N rules by trigger count."""
        sorted_rules = sorted(
            self._decisions_by_rule.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        return sorted_rules[:n]

    def reset(self) -> None:
        """Reset all metrics to initial state."""
        with self._lock:
            self._total_decisions = 0
            self._decisions_by_action.clear()
            self._decisions_by_mode.clear()
            self._decisions_by_rule.clear()
            self._blocked_total = 0
            self._modified_total = 0
            self._escalated_total = 0
            self._allowed_total = 0
            self._blocked_by_mode.clear()
            self._mode_transitions = 0
            self._mode_transition_history.clear()


# Global metrics instance
_governance_metrics: GovernanceMetrics | None = None
_metrics_lock = Lock()


def get_governance_metrics() -> GovernanceMetrics:
    """
    Get or create the global governance metrics instance.

    Returns:
        GovernanceMetrics singleton instance
    """
    global _governance_metrics

    if _governance_metrics is None:
        with _metrics_lock:
            if _governance_metrics is None:
                _governance_metrics = GovernanceMetrics()

    return _governance_metrics


def record_governance_decision(decision: GovernanceDecision) -> None:
    """
    Record a governance decision to metrics.

    This is the main convenience function for recording decisions.
    Safe to call even if metrics are not configured.

    Args:
        decision: GovernanceDecision from evaluate()
    """
    try:
        metrics = get_governance_metrics()
        metrics.record_decision(decision)

        # Log the decision at appropriate level
        log_level = logging.INFO
        if decision.action == "block":
            log_level = logging.WARNING
        elif decision.action == "escalate":
            log_level = logging.ERROR

        _logger.log(
            log_level,
            "Governance: action=%s rule=%s mode=%s",
            decision.action,
            decision.rule_id,
            decision.mode,
        )

    except Exception as e:
        # Graceful degradation - don't crash on metrics failure
        _logger.debug("Failed to record governance metrics: %s", e)


def set_governance_mode(mode: str) -> None:
    """
    Set the current governance operating mode.

    Args:
        mode: Mode name ("normal", "cautious", "emergency")
    """
    try:
        metrics = get_governance_metrics()
        metrics.set_mode(mode)
        _logger.info("Governance mode set to: %s", mode)
    except Exception as e:
        _logger.debug("Failed to set governance mode metric: %s", e)


def get_governance_summary() -> dict[str, Any]:
    """
    Get summary of governance metrics.

    Returns:
        Dictionary with summary statistics
    """
    return get_governance_metrics().get_summary()


def reset_governance_metrics() -> None:
    """Reset all governance metrics."""
    get_governance_metrics().reset()
