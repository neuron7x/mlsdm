"""Real-time performance monitoring."""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np
import psutil
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.types import ASGIApp


@dataclass
class PerformanceMetrics:
    """Real-time performance metrics."""

    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    throughput_rps: float
    error_rate_percent: float
    memory_mb: float


class PerformanceMonitor:
    """Real-time performance monitoring with alerting."""

    def __init__(self, window_size: int = 1000) -> None:
        """Initialize with sliding window."""
        self._latencies: deque[float] = deque(maxlen=window_size)
        self._errors: deque[bool] = deque(maxlen=window_size)
        self._start_time = time.time()
        self._request_count = 0

    def record_request(self, latency_ms: float, is_error: bool = False) -> None:
        """Record request metrics."""
        self._latencies.append(latency_ms)
        self._errors.append(is_error)
        self._request_count += 1

    def get_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        if not self._latencies:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0)

        latencies = np.array(self._latencies)

        return PerformanceMetrics(
            p50_latency_ms=float(np.percentile(latencies, 50)),
            p95_latency_ms=float(np.percentile(latencies, 95)),
            p99_latency_ms=float(np.percentile(latencies, 99)),
            throughput_rps=self._calculate_throughput(),
            error_rate_percent=self._calculate_error_rate(),
            memory_mb=self._get_memory_usage(),
        )

    def _calculate_throughput(self) -> float:
        """Calculate requests per second."""
        elapsed = time.time() - self._start_time
        if elapsed == 0:
            return 0.0
        return self._request_count / elapsed

    def _calculate_error_rate(self) -> float:
        """Calculate error rate percentage."""
        if not self._errors:
            return 0.0
        return (sum(self._errors) / len(self._errors)) * 100

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        process = psutil.Process()
        return float(process.memory_info().rss) / 1024 / 1024

    def check_slo_compliance(self) -> tuple[bool, list[str]]:
        """Check SLO compliance and return violations."""
        metrics = self.get_metrics()
        violations = []

        if metrics.p50_latency_ms > 30:
            violations.append(
                f"P50 latency {metrics.p50_latency_ms:.2f}ms > 30ms SLO"
            )

        if metrics.p95_latency_ms > 120:
            violations.append(
                f"P95 latency {metrics.p95_latency_ms:.2f}ms > 120ms SLO"
            )

        if metrics.p99_latency_ms > 200:
            violations.append(
                f"P99 latency {metrics.p99_latency_ms:.2f}ms > 200ms SLO"
            )

        if metrics.error_rate_percent > 1.0:
            violations.append(
                f"Error rate {metrics.error_rate_percent:.2f}% > 1.0% SLO"
            )

        return len(violations) == 0, violations


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic performance monitoring."""

    def __init__(self, app: ASGIApp, monitor: PerformanceMonitor) -> None:
        super().__init__(app)
        self.monitor = monitor

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Monitor each request."""
        start = time.perf_counter()

        try:
            response = await call_next(request)
            is_error = response.status_code >= 500
        except Exception:
            is_error = True
            raise
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            self.monitor.record_request(latency_ms, is_error)

        return response
