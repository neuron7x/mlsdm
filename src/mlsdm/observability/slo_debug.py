"""SLO debug instrumentation helpers.

This module provides lightweight, opt-in timing and counter logging for
performance/SLO validation. Logging is disabled by default and can be
enabled by setting MLSDM_SLO_DEBUG=1.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import Counter
from typing import Any

logger = logging.getLogger("mlsdm.slo_debug")

_SLO_DEBUG_ENABLED = os.getenv("MLSDM_SLO_DEBUG", "0") == "1"

_status_counts: Counter[int] = Counter()
_exception_counts: Counter[str] = Counter()
_active_requests = 0
_max_active_requests = 0
_lock = threading.Lock()


def slo_debug_enabled() -> bool:
    return _SLO_DEBUG_ENABLED


def start_slo_timer(endpoint: str) -> int | None:
    if not _SLO_DEBUG_ENABLED:
        return None

    global _active_requests, _max_active_requests
    with _lock:
        _active_requests += 1
        if _active_requests > _max_active_requests:
            _max_active_requests = _active_requests
        active = _active_requests
        max_active = _max_active_requests

    logger.info(
        json.dumps(
            {
                "event": "slo_request_start",
                "endpoint": endpoint,
                "active_requests": active,
                "max_active_requests": max_active,
                "ts": time.time(),
            }
        )
    )
    return time.monotonic_ns()


def finish_slo_timer(
    endpoint: str,
    start_ns: int | None,
    status_code: int,
    exception: BaseException | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    if not _SLO_DEBUG_ENABLED:
        return

    duration_ms = None
    if start_ns is not None:
        duration_ms = (time.monotonic_ns() - start_ns) / 1_000_000.0

    exc_name = type(exception).__name__ if exception is not None else None

    global _active_requests
    with _lock:
        _status_counts[status_code] += 1
        if exc_name:
            _exception_counts[exc_name] += 1
        _active_requests = max(0, _active_requests - 1)
        active = _active_requests
        status_counts = dict(_status_counts)
        exception_counts = dict(_exception_counts)

    payload = {
        "event": "slo_request_end",
        "endpoint": endpoint,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "exception": exc_name,
        "active_requests": active,
        "status_counts": status_counts,
        "exception_counts": exception_counts,
        "ts": time.time(),
    }
    if extra:
        payload.update(extra)

    logger.info(json.dumps(payload))
