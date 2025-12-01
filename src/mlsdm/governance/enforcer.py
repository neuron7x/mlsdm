"""
Governance Enforcer for MLSDM.

This module provides the core governance enforcement logic that applies
policies from policy.yaml to input/output payloads.

The enforcer:
1. Loads policy configuration from YAML
2. Evaluates input and output payloads against governance rules
3. Returns clear decisions with reasons and rule references
4. Supports three operating modes: normal, cautious, emergency

Usage:
    from mlsdm.governance.enforcer import evaluate, apply_decision

    decision = evaluate(
        input_payload={"prompt": "user question"},
        output_payload={"response": "LLM answer"},
        context={"moral_value": 0.8, "mode": "normal"}
    )

    if decision.action != "allow":
        output_payload = apply_decision(decision, output_payload)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_logger = logging.getLogger(__name__)

# Path to policy file (relative to this module)
_POLICY_PATH = Path(__file__).parent / "policy.yaml"


@dataclass
class GovernanceDecision:
    """
    Result of governance evaluation.

    Attributes:
        action: The action to take ("allow" | "block" | "modify" | "escalate")
        reason: Human-readable explanation of the decision
        rule_id: ID of the matching rule (e.g., "R001"), or None for default
        mode: Current operating mode ("normal" | "cautious" | "emergency")
        metadata: Additional context about the decision
    """

    action: str  # "allow" | "block" | "modify" | "escalate"
    reason: str
    rule_id: str | None
    mode: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyConfig:
    """
    Loaded policy configuration.

    Attributes:
        modes: Dictionary of mode configurations
        rules: List of governance rules
        signals: Signal definitions
        mode_selection: Mode selection criteria
    """

    modes: dict[str, dict[str, Any]]
    rules: list[dict[str, Any]]
    signals: dict[str, dict[str, Any]]
    mode_selection: dict[str, Any]


# Cache for loaded policy
_policy_cache: PolicyConfig | None = None


def _load_policy(policy_path: Path | None = None) -> PolicyConfig:
    """
    Load policy configuration from YAML file.

    Args:
        policy_path: Optional custom path to policy file

    Returns:
        PolicyConfig object with loaded configuration

    Raises:
        FileNotFoundError: If policy file doesn't exist
        ValueError: If policy file is invalid
    """
    global _policy_cache

    path = policy_path or _POLICY_PATH

    # Return cached policy if already loaded
    if _policy_cache is not None and policy_path is None:
        return _policy_cache

    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("Policy file must contain a YAML dictionary")

    # Validate required sections
    required_sections = ["modes", "rules"]
    for section in required_sections:
        if section not in data:
            raise ValueError(f"Policy file missing required section: {section}")

    policy = PolicyConfig(
        modes=data.get("modes", {}),
        rules=data.get("rules", []),
        signals=data.get("signals", {}),
        mode_selection=data.get("mode_selection", {}),
    )

    # Cache the policy
    if policy_path is None:
        _policy_cache = policy

    return policy


def reload_policy() -> PolicyConfig:
    """
    Force reload of policy from disk.

    Returns:
        Freshly loaded PolicyConfig
    """
    global _policy_cache
    _policy_cache = None
    return _load_policy()


def get_mode_config(mode: str, policy: PolicyConfig | None = None) -> dict[str, Any]:
    """
    Get configuration for a specific operating mode.

    Args:
        mode: Mode name ("normal", "cautious", "emergency")
        policy: Optional PolicyConfig (loads default if None)

    Returns:
        Mode configuration dictionary

    Raises:
        ValueError: If mode is not defined in policy
    """
    if policy is None:
        policy = _load_policy()

    if mode not in policy.modes:
        valid_modes = list(policy.modes.keys())
        raise ValueError(f"Unknown mode '{mode}'. Valid modes: {valid_modes}")

    return policy.modes[mode]


def _get_signal_value(
    signal_name: str,
    context: dict[str, Any],
    policy: PolicyConfig,
) -> Any:
    """
    Get signal value from context with defaults from policy.

    Args:
        signal_name: Name of the signal
        context: Context dictionary containing signal values
        policy: Loaded policy configuration

    Returns:
        Signal value from context or default
    """
    if signal_name in context:
        return context[signal_name]

    # Get default from policy signals
    if signal_name in policy.signals:
        return policy.signals[signal_name].get("default")

    return None


def _evaluate_condition(
    condition: str,
    context: dict[str, Any],
    mode_config: dict[str, Any],
    policy: PolicyConfig,
) -> bool:
    """
    Evaluate a rule condition against context.

    This is a simplified condition evaluator that handles common patterns.
    For production, consider using a proper expression parser.

    Args:
        condition: Condition string from rule
        context: Context with signal values
        mode_config: Current mode configuration
        policy: Loaded policy configuration

    Returns:
        True if condition matches, False otherwise
    """
    # Handle always-true condition (default rule)
    if condition == "true":
        return True

    # Build evaluation context with signals and mode
    eval_context: dict[str, Any] = {}

    # Add mode values with "mode." prefix replaced
    for key, value in mode_config.items():
        eval_context[f"mode_{key}"] = value

    # Add signal values
    for signal_name in policy.signals:
        eval_context[signal_name] = _get_signal_value(signal_name, context, policy)

    # Simple condition parsing for common patterns
    # Replace "mode." with "mode_" for evaluation
    eval_condition = condition.replace("mode.", "mode_")

    # Replace boolean literals (YAML uses lowercase)
    eval_condition = eval_condition.replace(" == true", " == True")
    eval_condition = eval_condition.replace(" == false", " == False")
    eval_condition = eval_condition.replace("(true)", "(True)")
    eval_condition = eval_condition.replace("(false)", "(False)")

    # Add True/False to evaluation context
    eval_context["True"] = True
    eval_context["False"] = False

    try:
        # Safe evaluation using restricted namespace
        result = eval(eval_condition, {"__builtins__": {}}, eval_context)  # noqa: S307
        return bool(result)
    except Exception as e:
        _logger.warning("Condition evaluation failed for '%s': %s", condition, e)
        return False


def evaluate(
    input_payload: dict[str, Any],
    output_payload: dict[str, Any] | None,
    context: dict[str, Any],
) -> GovernanceDecision:
    """
    Evaluate input/output payloads against governance policy.

    This is the main entry point for governance evaluation. It:
    1. Determines the operating mode from context
    2. Evaluates rules in priority order
    3. Returns the first matching rule's action

    Args:
        input_payload: Input data (prompt, request parameters)
        output_payload: Output data (response), or None for pre-flight check
        context: Additional context including:
            - mode: Operating mode ("normal", "cautious", "emergency")
            - moral_value: Moral score (0.0-1.0)
            - toxicity_score: Toxicity score (0.0-1.0)
            - pii_detected: Boolean for PII presence
            - risk_score: Overall risk score (0.0-1.0)
            - uncertainty_score: Model uncertainty (0.0-1.0)

    Returns:
        GovernanceDecision with action, reason, and metadata
    """
    # Load policy
    policy = _load_policy()

    # Get operating mode (default to "normal")
    mode = context.get("mode", "normal")

    # Validate mode
    if mode not in policy.modes:
        _logger.warning("Unknown mode '%s', falling back to 'normal'", mode)
        mode = "normal"

    mode_config = policy.modes[mode]

    # Sort rules by priority (higher priority first)
    sorted_rules = sorted(
        [r for r in policy.rules if r.get("enabled", True)],
        key=lambda r: r.get("priority", 0),
        reverse=True,
    )

    # Evaluate rules in order
    for rule in sorted_rules:
        rule_id = rule.get("id", "unknown")
        condition = rule.get("trigger", {}).get("condition", "false")

        if _evaluate_condition(condition, context, mode_config, policy):
            action = rule.get("action", "allow")
            description = rule.get("description", "No description")
            log_level = rule.get("log_level", "info")

            # Build metadata
            metadata: dict[str, Any] = {
                "rule_metadata": rule.get("metadata", {}),
                "mode_config": {
                    "moral_threshold": mode_config.get("moral_threshold"),
                    "toxicity_threshold": mode_config.get("toxicity_threshold"),
                },
            }

            # Add modification info if applicable
            if action == "modify":
                metadata["modification"] = rule.get("modification")
                metadata["disclaimer_text"] = rule.get("disclaimer_text")

            # Add response message if blocking/escalating
            if action in ("block", "escalate"):
                metadata["response_message"] = rule.get(
                    "response_message",
                    "Request cannot be processed."
                )

            # Log the decision
            log_fn = getattr(_logger, log_level, _logger.info)
            log_fn(
                "Governance decision: rule=%s action=%s mode=%s reason=%s",
                rule_id,
                action,
                mode,
                description,
            )

            return GovernanceDecision(
                action=action,
                reason=description,
                rule_id=rule_id,
                mode=mode,
                metadata=metadata,
            )

    # Should not reach here if policy has a default allow rule
    return GovernanceDecision(
        action="allow",
        reason="No matching rule found (default allow)",
        rule_id=None,
        mode=mode,
        metadata={},
    )


def apply_decision(
    decision: GovernanceDecision,
    output_payload: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """
    Apply governance decision to output payload.

    This function modifies or blocks output based on the decision:
    - allow: Returns output unchanged
    - block: Returns None (no output)
    - modify: Returns modified output (e.g., with disclaimer)
    - escalate: Returns None and flags for human review

    Args:
        decision: GovernanceDecision from evaluate()
        output_payload: Original output payload

    Returns:
        Modified output payload, or None if blocked/escalated
    """
    if decision.action == "allow":
        return output_payload

    if decision.action == "block":
        _logger.info(
            "Blocking output: rule=%s reason=%s",
            decision.rule_id,
            decision.reason,
        )
        return None

    if decision.action == "escalate":
        _logger.warning(
            "Escalating for human review: rule=%s reason=%s",
            decision.rule_id,
            decision.reason,
        )
        # In production, this would trigger a webhook or queue for review
        return None

    if decision.action == "modify":
        if output_payload is None:
            return None

        modified = output_payload.copy()
        modification_type = decision.metadata.get("modification")

        if modification_type == "add_disclaimer":
            disclaimer = decision.metadata.get(
                "disclaimer_text",
                "Note: This content may require verification."
            )
            response = modified.get("response", "")
            modified["response"] = f"{response}\n\n{disclaimer}"
            modified["governance_modified"] = True
            modified["governance_disclaimer_added"] = True

        elif modification_type == "redact_pii":
            # Placeholder for PII redaction
            # In production, use a proper PII detection/redaction library
            modified["governance_modified"] = True
            modified["governance_pii_redacted"] = True

        _logger.info(
            "Modified output: rule=%s modification=%s",
            decision.rule_id,
            modification_type,
        )

        return modified

    # Unknown action - default to allow
    _logger.warning("Unknown governance action: %s", decision.action)
    return output_payload


def select_mode(context: dict[str, Any]) -> str:
    """
    Automatically select operating mode based on context.

    This function implements the mode selection logic from policy:
    - Switches to emergency mode on critical thresholds
    - Switches to cautious mode for sensitive contexts
    - Falls back to normal mode otherwise

    Args:
        context: Context containing:
            - consecutive_rejections: Number of recent rejections
            - rejection_rate: Recent rejection rate
            - memory_usage_percent: Current memory usage
            - request_context: List of context tags (e.g., ["medical"])

    Returns:
        Selected mode name
    """
    policy = _load_policy()
    mode_selection = policy.mode_selection

    # Check emergency triggers
    emergency_triggers = mode_selection.get("emergency_triggers", {})

    if context.get("consecutive_rejections", 0) >= emergency_triggers.get(
        "consecutive_rejections", 100
    ):
        _logger.warning("Emergency mode triggered: consecutive rejections exceeded")
        return "emergency"

    if context.get("rejection_rate", 0) >= emergency_triggers.get(
        "rejection_rate_5min", 0.8
    ):
        _logger.warning("Emergency mode triggered: rejection rate exceeded")
        return "emergency"

    if context.get("memory_usage_percent", 0) >= emergency_triggers.get(
        "memory_usage_percent", 95
    ):
        _logger.warning("Emergency mode triggered: memory usage exceeded")
        return "emergency"

    # Check cautious contexts
    cautious_contexts = mode_selection.get("cautious_contexts", [])
    request_context = context.get("request_context", [])

    if any(ctx in cautious_contexts for ctx in request_context):
        return "cautious"

    # Default mode
    default_mode: str = mode_selection.get("default_mode", "normal")
    return default_mode


def get_current_mode_config() -> dict[str, Any]:
    """
    Get configuration for the default operating mode.

    Returns:
        Mode configuration dictionary for 'normal' mode
    """
    return get_mode_config("normal")


def clear_policy_cache() -> None:
    """Clear the policy cache, forcing reload on next access."""
    global _policy_cache
    _policy_cache = None
