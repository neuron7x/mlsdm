"""Performance-optimized moral filter with zero-allocation fast path."""
from __future__ import annotations

from dataclasses import dataclass
import logging

import numpy as np


@dataclass(frozen=True, slots=True)
class FilterDecision:
    """Immutable filter decision (zero-copy)."""

    accepted: bool
    score: float
    threshold: float


class MoralFilterV3:
    """Zero-overhead moral filter with optimized hot path."""

    __slots__ = (
        "_threshold",
        "_drift_buffer",
        "_drift_idx",
        "_drift_enabled",
        "_fast_path_enabled",
    )

    def __init__(
        self,
        threshold: float = 0.5,
        enable_drift_detection: bool = False,
        enable_fast_path: bool = True,
    ) -> None:
        """Initialize with performance-first defaults."""
        self._threshold = float(threshold)
        self._drift_enabled = enable_drift_detection
        self._fast_path_enabled = enable_fast_path

        if enable_drift_detection:
            self._drift_buffer = np.zeros(20, dtype=np.float32)
            self._drift_idx = 0
        else:
            self._drift_buffer = None
            self._drift_idx = 0

    @property
    def threshold(self) -> float:
        """Return current threshold."""
        return float(self._threshold)

    def filter(self, moral_score: float) -> FilterDecision:
        """Filter with zero-allocation fast path.

        Fast path: no drift detection, no logging, pure computation.
        Slow path: full drift detection and diagnostics.
        """
        if self._fast_path_enabled:
            # Fast path: single comparison, no allocations beyond decision
            return FilterDecision(
                accepted=moral_score >= self._threshold,
                score=moral_score,
                threshold=self._threshold,
            )

        # Slow path: full drift detection
        if self._drift_enabled:
            self._update_drift_buffer(moral_score)
            if self._detect_sustained_drift():
                self._log_drift_warning()

        return FilterDecision(
            accepted=moral_score >= self._threshold,
            score=moral_score,
            threshold=self._threshold,
        )

    def evaluate(self, moral_score: float) -> bool:
        """Compatibility wrapper returning acceptance boolean."""
        return self.filter(moral_score).accepted

    def adapt(self, accepted: bool) -> None:
        """Compatibility no-op for adaptive thresholds."""
        _ = accepted

    def get_state(self) -> dict[str, float]:
        """Expose minimal filter state."""
        return {
            "threshold": float(self._threshold),
        }

    def _update_drift_buffer(self, score: float) -> None:
        """Update drift buffer with circular index."""
        if self._drift_buffer is not None:
            self._drift_buffer[self._drift_idx] = score
            self._drift_idx = (self._drift_idx + 1) % len(self._drift_buffer)

    def _detect_sustained_drift(self) -> bool:
        """Check for sustained drift (optimized)."""
        if self._drift_buffer is None:
            return False

        # Use numpy for vectorized operations
        std = float(np.std(self._drift_buffer))
        return std > 0.1  # Threshold for sustained drift

    def _log_drift_warning(self) -> None:
        """Log drift warning (only in slow path)."""
        logging.getLogger(__name__).debug("Sustained drift detected in moral filter")
