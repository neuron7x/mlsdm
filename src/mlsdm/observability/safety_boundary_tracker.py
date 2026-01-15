"""Deterministic safety boundary hit tracking for guardrail enforcement.

Tracks recent safety boundary hits per actor and emits escalation decisions
without relying on wall-clock time. This provides bounded detection windows
in operation count and supports deterministic quarantine actions.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from threading import Lock

from prometheus_client import Counter, Gauge

logger = logging.getLogger(__name__)


_boundary_hits_total = Counter(
    "mlsdm_safety_boundary_hits_total",
    "Total safety boundary hits recorded by key",
    ["key", "result"],
)

_boundary_quarantine_total = Counter(
    "mlsdm_safety_boundary_quarantine_total",
    "Total safety boundary quarantine actions executed",
    ["key", "reason"],
)

_boundary_window_hit_ratio = Gauge(
    "mlsdm_safety_boundary_window_hit_ratio",
    "Ratio of boundary hits within the bounded decision window",
    ["key"],
)


@dataclass(frozen=True)
class SafetyBoundaryEnforcement:
    """Decision produced by the safety boundary tracker."""

    triggered: bool
    action: str | None
    hit_count: int
    window_size: int
    reason: str | None = None


class SafetyBoundaryTracker:
    """Stateful tracker for repeated safety boundary hits."""

    def __init__(self, window_size: int = 10, trigger_count: int = 3) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        if trigger_count <= 0:
            raise ValueError("trigger_count must be positive")
        if trigger_count > window_size:
            raise ValueError("trigger_count must not exceed window_size")
        self._window_size = window_size
        self._trigger_count = trigger_count
        self._lock = Lock()
        self._windows: dict[str, deque[bool]] = {}

    def record_decision(self, key: str, allowed: bool) -> SafetyBoundaryEnforcement:
        """Record a decision outcome and return enforcement decision."""
        with self._lock:
            window = self._windows.setdefault(key, deque(maxlen=self._window_size))
            window.append(not allowed)
            hit_count = sum(window)

        _boundary_hits_total.labels(key=key, result="denied" if not allowed else "allowed").inc()
        if window:
            _boundary_window_hit_ratio.labels(key=key).set(hit_count / self._window_size)

        if hit_count >= self._trigger_count:
            reason = "repeated_denials"
            _boundary_quarantine_total.labels(key=key, reason=reason).inc()
            logger.warning(
                "Safety boundary quarantine triggered for key=%s hits=%d/%d",
                key,
                hit_count,
                self._window_size,
            )
            return SafetyBoundaryEnforcement(
                triggered=True,
                action="quarantine",
                hit_count=hit_count,
                window_size=self._window_size,
                reason=reason,
            )

        return SafetyBoundaryEnforcement(
            triggered=False,
            action=None,
            hit_count=hit_count,
            window_size=self._window_size,
        )

    def reset(self, key: str | None = None) -> None:
        """Reset tracking state for a key or all keys."""
        with self._lock:
            if key is None:
                self._windows.clear()
            else:
                self._windows.pop(key, None)

    def snapshot(self, key: str) -> tuple[int, int]:
        """Return (hit_count, window_size) for a key."""
        with self._lock:
            window = self._windows.get(key)
            if not window:
                return (0, self._window_size)
            return (sum(window), self._window_size)


_tracker = SafetyBoundaryTracker()


def record_safety_boundary_decision(key: str, allowed: bool) -> SafetyBoundaryEnforcement:
    """Record a safety boundary decision for a key."""
    return _tracker.record_decision(key, allowed)


def reset_safety_boundary_tracker(key: str | None = None) -> None:
    """Reset the global safety boundary tracker."""
    _tracker.reset(key)


def snapshot_safety_boundary_tracker(key: str) -> tuple[int, int]:
    """Snapshot the hit count for a key."""
    return _tracker.snapshot(key)
