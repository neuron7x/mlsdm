"""Prometheus-compatible metrics for observability.

This module provides counters, gauges, and histograms for monitoring
the MLSDM cognitive architecture system, with Prometheus export format.
"""

import time
from enum import Enum
from threading import Lock
from typing import Any

from prometheus_client import (
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)


class PhaseType(Enum):
    """Cognitive rhythm phase types."""

    WAKE = "wake"
    SLEEP = "sleep"
    UNKNOWN = "unknown"


class MetricsExporter:
    """Prometheus-compatible metrics exporter for MLSDM system.

    Provides:
    - Counters: events_processed, events_rejected, errors
    - Gauges: current_memory_usage, moral_threshold, phase
    - Histograms: processing_latency_ms, retrieval_latency_ms
    """

    def __init__(self, registry: CollectorRegistry | None = None):
        """Initialize metrics exporter.

        Args:
            registry: Optional custom Prometheus registry. If None, uses default.
        """
        self.registry = registry or CollectorRegistry()
        self._lock = Lock()

        # Counters
        self.events_processed = Counter(
            "mlsdm_events_processed_total",
            "Total number of events processed by the system",
            registry=self.registry,
        )

        self.events_rejected = Counter(
            "mlsdm_events_rejected_total",
            "Total number of events rejected by moral filter",
            registry=self.registry,
        )

        self.errors = Counter(
            "mlsdm_errors_total",
            "Total number of errors encountered",
            ["error_type"],
            registry=self.registry,
        )

        # Gauges
        self.current_memory_usage = Gauge(
            "mlsdm_memory_usage_bytes",
            "Current memory usage in bytes",
            registry=self.registry,
        )

        self.moral_threshold = Gauge(
            "mlsdm_moral_threshold",
            "Current moral filter threshold value",
            registry=self.registry,
        )

        self.phase_gauge = Gauge(
            "mlsdm_phase",
            "Current cognitive rhythm phase (0=sleep, 1=wake)",
            registry=self.registry,
        )

        self.memory_l1_norm = Gauge(
            "mlsdm_memory_l1_norm",
            "L1 memory layer norm",
            registry=self.registry,
        )

        self.memory_l2_norm = Gauge(
            "mlsdm_memory_l2_norm",
            "L2 memory layer norm",
            registry=self.registry,
        )

        self.memory_l3_norm = Gauge(
            "mlsdm_memory_l3_norm",
            "L3 memory layer norm",
            registry=self.registry,
        )

        # Histograms with reasonable buckets for millisecond latencies
        self.processing_latency_ms = Histogram(
            "mlsdm_processing_latency_milliseconds",
            "Event processing latency in milliseconds",
            buckets=(1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000),
            registry=self.registry,
        )

        self.retrieval_latency_ms = Histogram(
            "mlsdm_retrieval_latency_milliseconds",
            "Memory retrieval latency in milliseconds",
            buckets=(0.1, 0.5, 1, 2.5, 5, 10, 25, 50, 100, 250, 500),
            registry=self.registry,
        )

        # Track timing contexts
        self._processing_start_times: dict[str, float] = {}
        self._retrieval_start_times: dict[str, float] = {}

    def increment_events_processed(self, count: int = 1) -> None:
        """Increment the events processed counter.

        Args:
            count: Number of events to add (default: 1)
        """
        with self._lock:
            self.events_processed.inc(count)

    def increment_events_rejected(self, count: int = 1) -> None:
        """Increment the events rejected counter.

        Args:
            count: Number of events to add (default: 1)
        """
        with self._lock:
            self.events_rejected.inc(count)

    def increment_errors(self, error_type: str, count: int = 1) -> None:
        """Increment the errors counter.

        Args:
            error_type: Type/category of error
            count: Number of errors to add (default: 1)
        """
        with self._lock:
            self.errors.labels(error_type=error_type).inc(count)

    def set_memory_usage(self, bytes_used: float) -> None:
        """Set current memory usage.

        Args:
            bytes_used: Memory usage in bytes
        """
        with self._lock:
            self.current_memory_usage.set(bytes_used)

    def set_moral_threshold(self, threshold: float) -> None:
        """Set current moral threshold.

        Args:
            threshold: Moral filter threshold value
        """
        with self._lock:
            self.moral_threshold.set(threshold)

    def set_phase(self, phase: PhaseType | str) -> None:
        """Set current cognitive rhythm phase.

        Args:
            phase: Current phase (wake=1, sleep=0)
        """
        with self._lock:
            if isinstance(phase, str):
                phase = PhaseType(phase.lower())

            # Map phase to numeric value for gauge
            phase_value = 1.0 if phase == PhaseType.WAKE else 0.0
            self.phase_gauge.set(phase_value)

    def set_memory_norms(self, l1_norm: float, l2_norm: float, l3_norm: float) -> None:
        """Set memory layer norms.

        Args:
            l1_norm: L1 layer norm
            l2_norm: L2 layer norm
            l3_norm: L3 layer norm
        """
        with self._lock:
            self.memory_l1_norm.set(l1_norm)
            self.memory_l2_norm.set(l2_norm)
            self.memory_l3_norm.set(l3_norm)

    def start_processing_timer(self, correlation_id: str) -> None:
        """Start timing an event processing operation.

        Args:
            correlation_id: Unique identifier for this processing operation
        """
        with self._lock:
            self._processing_start_times[correlation_id] = time.monotonic()

    def stop_processing_timer(self, correlation_id: str) -> float | None:
        """Stop timing an event processing operation and record the latency.

        Args:
            correlation_id: Unique identifier for this processing operation

        Returns:
            The latency in milliseconds, or None if timer wasn't started
        """
        with self._lock:
            start_time = self._processing_start_times.pop(correlation_id, None)
            if start_time is None:
                return None

            latency_seconds = time.monotonic() - start_time
            latency_ms = latency_seconds * 1000
            self.processing_latency_ms.observe(latency_ms)
            return latency_ms

    def observe_processing_latency(self, latency_ms: float) -> None:
        """Directly observe a processing latency value.

        Args:
            latency_ms: Processing latency in milliseconds
        """
        with self._lock:
            self.processing_latency_ms.observe(latency_ms)

    def start_retrieval_timer(self, correlation_id: str) -> None:
        """Start timing a memory retrieval operation.

        Args:
            correlation_id: Unique identifier for this retrieval operation
        """
        with self._lock:
            self._retrieval_start_times[correlation_id] = time.monotonic()

    def stop_retrieval_timer(self, correlation_id: str) -> float | None:
        """Stop timing a memory retrieval operation and record the latency.

        Args:
            correlation_id: Unique identifier for this retrieval operation

        Returns:
            The latency in milliseconds, or None if timer wasn't started
        """
        with self._lock:
            start_time = self._retrieval_start_times.pop(correlation_id, None)
            if start_time is None:
                return None

            latency_seconds = time.monotonic() - start_time
            latency_ms = latency_seconds * 1000
            self.retrieval_latency_ms.observe(latency_ms)
            return latency_ms

    def observe_retrieval_latency(self, latency_ms: float) -> None:
        """Directly observe a retrieval latency value.

        Args:
            latency_ms: Retrieval latency in milliseconds
        """
        with self._lock:
            self.retrieval_latency_ms.observe(latency_ms)

    def export_metrics(self) -> bytes:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics as bytes
        """
        return generate_latest(self.registry)

    def get_metrics_text(self) -> str:
        """Export metrics in Prometheus format as text.

        Returns:
            Prometheus-formatted metrics as string
        """
        return self.export_metrics().decode("utf-8")

    def get_current_values(self) -> dict[str, Any]:
        """Get current metric values as a dictionary.

        Returns:
            Dictionary with current metric values
        """
        # Note: Prometheus client doesn't provide easy access to current values
        # This is a convenience method that returns what we can track
        return {
            "events_processed": self.events_processed._value.get(),
            "events_rejected": self.events_rejected._value.get(),
            "memory_usage_bytes": self.current_memory_usage._value.get(),
            "moral_threshold": self.moral_threshold._value.get(),
            "phase": self.phase_gauge._value.get(),
            "memory_l1_norm": self.memory_l1_norm._value.get(),
            "memory_l2_norm": self.memory_l2_norm._value.get(),
            "memory_l3_norm": self.memory_l3_norm._value.get(),
        }


# Global instance for convenience
_metrics_exporter: MetricsExporter | None = None
_metrics_exporter_lock = Lock()


def get_metrics_exporter(registry: CollectorRegistry | None = None) -> MetricsExporter:
    """Get or create the metrics exporter instance.

    This function is thread-safe and implements the singleton pattern.

    Args:
        registry: Optional custom Prometheus registry

    Returns:
        MetricsExporter instance
    """
    global _metrics_exporter

    # Double-checked locking pattern for thread-safe singleton
    if _metrics_exporter is None:
        with _metrics_exporter_lock:
            if _metrics_exporter is None:
                _metrics_exporter = MetricsExporter(registry=registry)

    return _metrics_exporter
