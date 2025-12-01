"""
MLSDM Governance Module.

This module provides policy-based content governance for the MLSDM cognitive engine,
including:
- Mode-based operational profiles (normal, cautious, emergency)
- Rule-based content evaluation (allow, block, modify, escalate)
- PII detection and protection
- Toxicity and moral threshold enforcement
- Metrics collection and audit logging

Usage:
    >>> from mlsdm.governance import evaluate, apply_decision, GovernanceDecision
    >>>
    >>> # Evaluate input before LLM generation
    >>> decision = evaluate(
    ...     input_payload={"prompt": "Hello", "moral_value": 0.5},
    ...     output_payload=None,
    ...     context={"risk_level": 0.3}
    ... )
    >>>
    >>> if decision.action == "block":
    ...     return {"error": decision.reason}
    >>>
    >>> # Generate response...
    >>>
    >>> # Evaluate and apply decision to output
    >>> decision = evaluate(input_payload, output_payload, context)
    >>> output_payload = apply_decision(decision, output_payload)

For more details, see docs/GOVERNANCE.md.
"""

from mlsdm.governance.enforcer import (
    ActionType,
    GovernanceContext,
    GovernanceDecision,
    LogLevel,
    PolicyLoader,
    apply_decision,
    evaluate,
    get_current_mode,
    reload_policy,
)
from mlsdm.governance.metrics import (
    GovernanceCounters,
    GovernanceMetrics,
    get_metrics,
    log_governance_event,
    record_decision,
    register_prometheus_metrics,
)

__all__ = [
    # Enforcer
    "evaluate",
    "apply_decision",
    "GovernanceDecision",
    "GovernanceContext",
    "PolicyLoader",
    "get_current_mode",
    "reload_policy",
    "ActionType",
    "LogLevel",
    # Metrics
    "get_metrics",
    "record_decision",
    "log_governance_event",
    "GovernanceMetrics",
    "GovernanceCounters",
    "register_prometheus_metrics",
]
