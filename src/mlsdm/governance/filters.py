"""
Governance Filters for LLM Pipeline Integration.

This module provides pre-filter and post-filter implementations that integrate
the governance enforcer with the LLMPipeline from llm_pipeline.py.

Usage:
    from mlsdm.core.llm_pipeline import LLMPipeline, PipelineConfig
    from mlsdm.governance.filters import GovernancePreFilter, GovernancePostFilter

    pipeline = LLMPipeline(...)

    # Add governance filters
    gov_pre = GovernancePreFilter(mode="normal")
    gov_post = GovernancePostFilter(mode="normal")
"""

from __future__ import annotations

import logging
from typing import Any

from mlsdm.governance.enforcer import (
    apply_decision,
    evaluate,
    select_mode,
)
from mlsdm.governance.metrics import (
    record_governance_decision,
    set_governance_mode,
)

_logger = logging.getLogger(__name__)


class GovernancePreFilter:
    """
    Pre-filter implementing governance evaluation.

    Evaluates input payloads against governance policy before LLM generation.
    Can block requests based on moral value, toxicity, risk, or other signals.
    """

    def __init__(
        self,
        mode: str | None = None,
        auto_mode_selection: bool = False,
    ) -> None:
        """
        Initialize governance pre-filter.

        Args:
            mode: Operating mode ("normal", "cautious", "emergency").
                  If None, defaults to "normal".
            auto_mode_selection: If True, automatically select mode based on context.
        """
        self._mode = mode or "normal"
        self._auto_mode_selection = auto_mode_selection
        set_governance_mode(self._mode)

    def evaluate(
        self,
        prompt: str,
        context: dict[str, Any],
    ) -> "FilterResult":
        """
        Evaluate prompt against governance policy.

        Args:
            prompt: Input prompt text.
            context: Additional context including:
                - moral_value: Moral score (0.0-1.0)
                - toxicity_score: Toxicity score (0.0-1.0)
                - request_context: List of context tags for mode selection

        Returns:
            FilterResult with ALLOW, BLOCK, or MODIFY decision.
        """
        from mlsdm.core.llm_pipeline import FilterDecision, FilterResult

        # Auto-select mode if enabled
        mode = self._mode
        if self._auto_mode_selection:
            mode = select_mode(context)
            set_governance_mode(mode)

        # Build governance context
        gov_context = {
            **context,
            "mode": mode,
        }

        # Evaluate using governance enforcer
        decision = evaluate(
            input_payload={"prompt": prompt},
            output_payload=None,
            context=gov_context,
        )

        # Record metrics
        record_governance_decision(decision)

        # Map governance action to filter decision
        if decision.action == "allow":
            return FilterResult(
                decision=FilterDecision.ALLOW,
                reason="governance_approved",
                metadata={
                    "rule_id": decision.rule_id,
                    "mode": decision.mode,
                },
            )

        elif decision.action == "block":
            return FilterResult(
                decision=FilterDecision.BLOCK,
                reason=decision.reason,
                metadata={
                    "rule_id": decision.rule_id,
                    "mode": decision.mode,
                    "response_message": decision.metadata.get("response_message"),
                },
            )

        elif decision.action == "modify":
            # Pre-filter modification (rare for pre-flight)
            return FilterResult(
                decision=FilterDecision.MODIFY,
                reason=decision.reason,
                metadata={
                    "rule_id": decision.rule_id,
                    "mode": decision.mode,
                    "modification": decision.metadata.get("modification"),
                },
            )

        elif decision.action == "escalate":
            # Treat escalation as block in pre-filter
            return FilterResult(
                decision=FilterDecision.BLOCK,
                reason=f"escalated: {decision.reason}",
                metadata={
                    "rule_id": decision.rule_id,
                    "mode": decision.mode,
                    "escalated": True,
                },
            )

        # Unknown action - default to allow
        return FilterResult(
            decision=FilterDecision.ALLOW,
            reason="unknown_governance_action",
            metadata={"action": decision.action},
        )

    def set_mode(self, mode: str) -> None:
        """
        Set the operating mode.

        Args:
            mode: Mode name ("normal", "cautious", "emergency")
        """
        self._mode = mode
        set_governance_mode(mode)


class GovernancePostFilter:
    """
    Post-filter implementing governance evaluation on LLM output.

    Evaluates output payloads against governance policy after LLM generation.
    Can modify or block responses based on content analysis.
    """

    def __init__(
        self,
        mode: str | None = None,
        auto_mode_selection: bool = False,
    ) -> None:
        """
        Initialize governance post-filter.

        Args:
            mode: Operating mode ("normal", "cautious", "emergency").
                  If None, defaults to "normal".
            auto_mode_selection: If True, automatically select mode based on context.
        """
        self._mode = mode or "normal"
        self._auto_mode_selection = auto_mode_selection

    def evaluate(
        self,
        response: str,
        context: dict[str, Any],
    ) -> "FilterResult":
        """
        Evaluate LLM response against governance policy.

        Args:
            response: Generated text from LLM.
            context: Additional context including:
                - prompt: Original prompt
                - max_tokens: Token limit
                - pii_detected: Boolean for PII presence
                - misinformation_score: Misinformation probability

        Returns:
            FilterResult with ALLOW, BLOCK, or MODIFY decision.
        """
        from mlsdm.core.llm_pipeline import FilterDecision, FilterResult

        # Auto-select mode if enabled
        mode = self._mode
        if self._auto_mode_selection:
            mode = select_mode(context)

        # Build governance context
        gov_context = {
            **context,
            "mode": mode,
        }

        # Evaluate using governance enforcer
        decision = evaluate(
            input_payload={"prompt": context.get("prompt", "")},
            output_payload={"response": response},
            context=gov_context,
        )

        # Record metrics
        record_governance_decision(decision)

        # Map governance action to filter decision
        if decision.action == "allow":
            return FilterResult(
                decision=FilterDecision.ALLOW,
                reason="governance_approved",
                metadata={
                    "rule_id": decision.rule_id,
                    "mode": decision.mode,
                },
            )

        elif decision.action == "block":
            return FilterResult(
                decision=FilterDecision.BLOCK,
                reason=decision.reason,
                metadata={
                    "rule_id": decision.rule_id,
                    "mode": decision.mode,
                    "response_message": decision.metadata.get("response_message"),
                },
            )

        elif decision.action == "modify":
            # Apply modification
            output_payload = {"response": response}
            modified = apply_decision(decision, output_payload)

            if modified is not None:
                modified_content = modified.get("response", response)
            else:
                modified_content = response

            return FilterResult(
                decision=FilterDecision.MODIFY,
                reason=decision.reason,
                modified_content=modified_content,
                metadata={
                    "rule_id": decision.rule_id,
                    "mode": decision.mode,
                    "modification": decision.metadata.get("modification"),
                    "original_response": response,
                },
            )

        elif decision.action == "escalate":
            # Treat escalation as block in post-filter
            return FilterResult(
                decision=FilterDecision.BLOCK,
                reason=f"escalated: {decision.reason}",
                metadata={
                    "rule_id": decision.rule_id,
                    "mode": decision.mode,
                    "escalated": True,
                },
            )

        # Unknown action - default to allow
        return FilterResult(
            decision=FilterDecision.ALLOW,
            reason="unknown_governance_action",
            metadata={"action": decision.action},
        )

    def set_mode(self, mode: str) -> None:
        """
        Set the operating mode.

        Args:
            mode: Mode name ("normal", "cautious", "emergency")
        """
        self._mode = mode
        set_governance_mode(mode)
