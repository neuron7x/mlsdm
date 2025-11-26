"""Observability module for MLSDM Governed Cognitive Memory.

This module provides structured logging and monitoring capabilities
for the cognitive architecture system.
"""

from .aphasia_logging import (
    LOGGER_NAME as APHASIA_LOGGER_NAME,
)
from .aphasia_logging import (
    AphasiaLogEvent,
    log_aphasia_event,
)
from .aphasia_logging import (
    get_logger as get_aphasia_logger,
)
from .aphasia_metrics import (
    AphasiaMetricsExporter,
    get_aphasia_metrics_exporter,
    reset_aphasia_metrics_exporter,
)
from .logger import (
    EventType,
    ObservabilityLogger,
    get_observability_logger,
)
from .metrics import (
    MetricsExporter,
    PhaseType,
    get_metrics_exporter,
)

__all__ = [
    # Aphasia-specific observability
    "APHASIA_LOGGER_NAME",
    "AphasiaLogEvent",
    "AphasiaMetricsExporter",
    # General observability
    "EventType",
    "MetricsExporter",
    "ObservabilityLogger",
    "PhaseType",
    "get_aphasia_logger",
    "get_aphasia_metrics_exporter",
    "get_metrics_exporter",
    "get_observability_logger",
    "log_aphasia_event",
    "reset_aphasia_metrics_exporter",
]
