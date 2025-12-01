"""
MLSDM Governance Module.

This module provides content governance and safety enforcement for the
MLSDM cognitive memory system. It includes:

- Policy configuration with modes (normal/cautious/emergency)
- Rule-based evaluation engine
- Decision enforcement (block/modify/escalate)
- Governance metrics and logging
- Pipeline filter integration

Components:
    - enforcer: Core evaluation and decision logic
    - metrics: Prometheus-compatible metrics collection
    - filters: Pre/post filters for LLMPipeline integration
    - policy.yaml: Declarative policy configuration

Usage:
    from mlsdm.governance import evaluate, apply_decision, GovernanceDecision

    # Evaluate a request
    decision = evaluate(
        input_payload={"prompt": "user question"},
        output_payload={"response": "LLM answer"},
        context={"moral_value": 0.8, "mode": "normal"},
    )

    # Apply the decision
    if decision.action != "allow":
        output = apply_decision(decision, output_payload)

For integration with LLMPipeline, use the GovernancePreFilter and
GovernancePostFilter classes.
"""

from mlsdm.governance.enforcer import (
    GovernanceDecision,
    PolicyConfig,
    apply_decision,
    clear_policy_cache,
    evaluate,
    get_current_mode_config,
    get_mode_config,
    reload_policy,
    select_mode,
)
from mlsdm.governance.filters import (
    GovernancePostFilter,
    GovernancePreFilter,
)
from mlsdm.governance.metrics import (
    GovernanceMetrics,
    get_governance_metrics,
    get_governance_summary,
    record_governance_decision,
    reset_governance_metrics,
    set_governance_mode,
)

__all__ = [
    # Core enforcer
    "GovernanceDecision",
    "PolicyConfig",
    "evaluate",
    "apply_decision",
    "get_mode_config",
    "get_current_mode_config",
    "select_mode",
    "reload_policy",
    "clear_policy_cache",
    # Filters
    "GovernancePreFilter",
    "GovernancePostFilter",
    # Metrics
    "GovernanceMetrics",
    "get_governance_metrics",
    "get_governance_summary",
    "record_governance_decision",
    "set_governance_mode",
    "reset_governance_metrics",
]
