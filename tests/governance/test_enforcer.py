"""
Tests for Governance Enforcer.

This test suite validates the governance enforcement layer including:
- Policy loading and validation
- Rule evaluation across modes
- Decision application (allow/block/modify/escalate)
- Mode selection logic
- Metrics recording
"""

import pytest

from mlsdm.governance import (
    GovernanceDecision,
    apply_decision,
    clear_policy_cache,
    evaluate,
    get_governance_metrics,
    get_governance_summary,
    get_mode_config,
    record_governance_decision,
    reset_governance_metrics,
    select_mode,
    set_governance_mode,
)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset governance state before each test."""
    clear_policy_cache()
    reset_governance_metrics()


class TestPolicyLoading:
    """Tests for policy loading and validation."""

    def test_policy_loads_successfully(self) -> None:
        """Policy file loads without errors."""
        config = get_mode_config("normal")
        assert config is not None
        assert "moral_threshold" in config

    def test_all_modes_defined(self) -> None:
        """All three modes are defined in policy."""
        for mode in ["normal", "cautious", "emergency"]:
            config = get_mode_config(mode)
            assert config is not None
            assert "moral_threshold" in config
            assert "toxicity_threshold" in config

    def test_mode_thresholds_ascending(self) -> None:
        """Emergency mode has highest threshold, normal has lowest."""
        normal = get_mode_config("normal")
        cautious = get_mode_config("cautious")
        emergency = get_mode_config("emergency")

        assert normal["moral_threshold"] < cautious["moral_threshold"]
        assert cautious["moral_threshold"] < emergency["moral_threshold"]

    def test_unknown_mode_raises_error(self) -> None:
        """Requesting unknown mode raises ValueError."""
        with pytest.raises(ValueError, match="Unknown mode"):
            get_mode_config("nonexistent_mode")


class TestBasicEvaluation:
    """Tests for basic evaluation scenarios."""

    def test_allow_high_moral_value(self) -> None:
        """High moral value should be allowed in normal mode."""
        decision = evaluate(
            input_payload={"prompt": "test"},
            output_payload={"response": "test response"},
            context={"moral_value": 0.9, "mode": "normal"},
        )

        assert decision.action == "allow"
        assert decision.mode == "normal"

    def test_block_low_moral_value(self) -> None:
        """Low moral value should be blocked."""
        decision = evaluate(
            input_payload={"prompt": "test"},
            output_payload={"response": "test response"},
            context={"moral_value": 0.2, "mode": "normal"},
        )

        assert decision.action == "block"
        assert decision.rule_id == "R002"
        assert "moral" in decision.reason.lower()

    def test_block_high_toxicity(self) -> None:
        """High toxicity should be blocked."""
        decision = evaluate(
            input_payload={"prompt": "test"},
            output_payload=None,
            context={"toxicity_score": 0.9, "mode": "normal"},
        )

        assert decision.action == "block"
        assert decision.rule_id == "R001"
        assert "toxicity" in decision.reason.lower()

    def test_default_mode_is_normal(self) -> None:
        """Missing mode defaults to normal."""
        decision = evaluate(
            input_payload={"prompt": "test"},
            output_payload=None,
            context={"moral_value": 0.9},  # No mode specified
        )

        assert decision.mode == "normal"


class TestModeVariations:
    """Tests for different operating modes."""

    def test_cautious_mode_stricter_threshold(self) -> None:
        """Cautious mode should block values that pass in normal mode."""
        # Value that passes in normal mode
        context_normal = {"moral_value": 0.55, "mode": "normal"}
        decision_normal = evaluate({}, None, context_normal)
        assert decision_normal.action == "allow"

        # Same value blocked in cautious mode
        context_cautious = {"moral_value": 0.55, "mode": "cautious"}
        decision_cautious = evaluate({}, None, context_cautious)
        assert decision_cautious.action == "block"

    def test_emergency_mode_strictest(self) -> None:
        """Emergency mode should have strictest thresholds."""
        # Value that passes in cautious mode
        context_cautious = {"moral_value": 0.70, "mode": "cautious"}
        decision_cautious = evaluate({}, None, context_cautious)
        assert decision_cautious.action == "allow"

        # Same value blocked in emergency mode
        context_emergency = {"moral_value": 0.70, "mode": "emergency"}
        decision_emergency = evaluate({}, None, context_emergency)
        assert decision_emergency.action == "block"

    def test_uncertainty_blocked_in_cautious_mode(self) -> None:
        """High uncertainty blocked in cautious mode but not normal."""
        # High uncertainty in normal mode - allowed (block_on_uncertainty=false)
        context_normal = {
            "moral_value": 0.8,
            "uncertainty_score": 0.75,
            "mode": "normal",
        }
        decision_normal = evaluate({}, None, context_normal)
        assert decision_normal.action == "allow"

        # High uncertainty in cautious mode - blocked
        context_cautious = {
            "moral_value": 0.8,
            "uncertainty_score": 0.75,
            "mode": "cautious",
        }
        decision_cautious = evaluate({}, None, context_cautious)
        assert decision_cautious.action == "block"


class TestSpecificRules:
    """Tests for specific governance rules."""

    def test_pii_detection_triggers_modify(self) -> None:
        """PII detection should trigger modification."""
        decision = evaluate(
            input_payload={"prompt": "test"},
            output_payload={"response": "contains PII"},
            context={"pii_detected": True, "mode": "normal"},
        )

        assert decision.action == "modify"
        assert decision.rule_id == "R003"
        assert "modification" in decision.metadata

    def test_high_risk_triggers_escalation(self) -> None:
        """High risk content should trigger escalation in cautious mode."""
        decision = evaluate(
            input_payload={"prompt": "test"},
            output_payload=None,
            context={"moral_value": 0.8, "risk_score": 0.85, "mode": "cautious"},
        )

        assert decision.action == "escalate"
        assert decision.rule_id == "R004"

    def test_misinformation_adds_disclaimer(self) -> None:
        """Misinformation should add disclaimer."""
        decision = evaluate(
            input_payload={"prompt": "test"},
            output_payload={"response": "dubious claim"},
            context={"misinformation_score": 0.7, "mode": "normal"},
        )

        assert decision.action == "modify"
        assert decision.rule_id == "R006"
        assert decision.metadata.get("modification") == "add_disclaimer"


class TestApplyDecision:
    """Tests for applying governance decisions."""

    def test_allow_returns_unchanged(self) -> None:
        """Allow decision returns payload unchanged."""
        output = {"response": "original"}
        decision = GovernanceDecision(
            action="allow",
            reason="test",
            rule_id=None,
            mode="normal",
        )

        result = apply_decision(decision, output)
        assert result == output

    def test_block_returns_none(self) -> None:
        """Block decision returns None."""
        output = {"response": "original"}
        decision = GovernanceDecision(
            action="block",
            reason="test",
            rule_id="R001",
            mode="normal",
        )

        result = apply_decision(decision, output)
        assert result is None

    def test_escalate_returns_none(self) -> None:
        """Escalate decision returns None."""
        output = {"response": "original"}
        decision = GovernanceDecision(
            action="escalate",
            reason="test",
            rule_id="R004",
            mode="cautious",
        )

        result = apply_decision(decision, output)
        assert result is None

    def test_modify_adds_disclaimer(self) -> None:
        """Modify with add_disclaimer updates response."""
        output = {"response": "original content"}
        decision = GovernanceDecision(
            action="modify",
            reason="test",
            rule_id="R006",
            mode="normal",
            metadata={
                "modification": "add_disclaimer",
                "disclaimer_text": "This is a test disclaimer.",
            },
        )

        result = apply_decision(decision, output)

        assert result is not None
        assert "This is a test disclaimer" in result["response"]
        assert result["governance_modified"] is True
        assert result["governance_disclaimer_added"] is True

    def test_modify_pii_redaction(self) -> None:
        """Modify with redact_pii marks as redacted."""
        output = {"response": "contains sensitive data"}
        decision = GovernanceDecision(
            action="modify",
            reason="test",
            rule_id="R003",
            mode="normal",
            metadata={"modification": "redact_pii"},
        )

        result = apply_decision(decision, output)

        assert result is not None
        assert result["governance_modified"] is True
        assert result["governance_pii_redacted"] is True

    def test_modify_with_none_payload(self) -> None:
        """Modify with None payload returns None."""
        decision = GovernanceDecision(
            action="modify",
            reason="test",
            rule_id="R003",
            mode="normal",
            metadata={"modification": "redact_pii"},
        )

        result = apply_decision(decision, None)
        assert result is None


class TestModeSelection:
    """Tests for automatic mode selection."""

    def test_default_mode_is_normal(self) -> None:
        """Default mode when no triggers is normal."""
        mode = select_mode({})
        assert mode == "normal"

    def test_emergency_on_consecutive_rejections(self) -> None:
        """Emergency mode triggered by high consecutive rejections."""
        mode = select_mode({"consecutive_rejections": 150})
        assert mode == "emergency"

    def test_emergency_on_high_rejection_rate(self) -> None:
        """Emergency mode triggered by high rejection rate."""
        mode = select_mode({"rejection_rate": 0.85})
        assert mode == "emergency"

    def test_emergency_on_high_memory(self) -> None:
        """Emergency mode triggered by high memory usage."""
        mode = select_mode({"memory_usage_percent": 98})
        assert mode == "emergency"

    def test_cautious_for_medical_context(self) -> None:
        """Cautious mode for medical context."""
        mode = select_mode({"request_context": ["medical"]})
        assert mode == "cautious"

    def test_cautious_for_financial_context(self) -> None:
        """Cautious mode for financial context."""
        mode = select_mode({"request_context": ["financial"]})
        assert mode == "cautious"

    def test_cautious_for_legal_context(self) -> None:
        """Cautious mode for legal context."""
        mode = select_mode({"request_context": ["legal"]})
        assert mode == "cautious"


class TestGovernanceMetrics:
    """Tests for governance metrics."""

    def test_record_decision_increments_total(self) -> None:
        """Recording decisions increments total counter."""
        decision = GovernanceDecision(
            action="allow",
            reason="test",
            rule_id="R007",
            mode="normal",
        )

        record_governance_decision(decision)

        summary = get_governance_summary()
        assert summary["total_decisions"] == 1

    def test_record_block_increments_block_counter(self) -> None:
        """Recording block decision increments block counter."""
        decision = GovernanceDecision(
            action="block",
            reason="test",
            rule_id="R001",
            mode="normal",
        )

        record_governance_decision(decision)

        metrics = get_governance_metrics()
        snapshot = metrics.get_snapshot()
        assert snapshot["blocked_total"] == 1

    def test_mode_tracking(self) -> None:
        """Mode changes are tracked."""
        set_governance_mode("normal")
        set_governance_mode("cautious")
        set_governance_mode("emergency")

        snapshot = get_governance_metrics().get_snapshot()
        assert snapshot["current_mode"] == "emergency"
        assert snapshot["mode_transitions"] == 2  # Two transitions

    def test_summary_calculates_rates(self) -> None:
        """Summary correctly calculates rates."""
        # Record 4 allows and 1 block
        for _ in range(4):
            record_governance_decision(
                GovernanceDecision("allow", "test", "R007", "normal")
            )
        record_governance_decision(
            GovernanceDecision("block", "test", "R001", "normal")
        )

        summary = get_governance_summary()
        assert summary["total_decisions"] == 5
        assert summary["allow_rate"] == 0.8
        assert summary["block_rate"] == 0.2


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_full_flow_allow(self) -> None:
        """Full flow for allowed content."""
        input_payload = {"prompt": "What is the weather today?"}
        output_payload = {"response": "It is sunny today."}
        context = {"moral_value": 0.85, "toxicity_score": 0.1, "mode": "normal"}

        # Evaluate
        decision = evaluate(input_payload, output_payload, context)
        assert decision.action == "allow"

        # Apply
        result = apply_decision(decision, output_payload)
        assert result == output_payload

        # Record
        record_governance_decision(decision)

    def test_full_flow_block(self) -> None:
        """Full flow for blocked content."""
        input_payload = {"prompt": "Generate harmful content"}
        output_payload = None  # Pre-flight check
        context = {"moral_value": 0.15, "toxicity_score": 0.9, "mode": "normal"}

        # Evaluate
        decision = evaluate(input_payload, output_payload, context)
        assert decision.action == "block"

        # Apply
        result = apply_decision(decision, output_payload)
        assert result is None

        # Record
        record_governance_decision(decision)

    def test_mode_transition_scenario(self) -> None:
        """Test mode transitions based on context."""
        # Start fresh for this test
        reset_governance_metrics()

        # Start in normal mode
        context1 = {}
        mode1 = select_mode(context1)
        assert mode1 == "normal"
        set_governance_mode(mode1)

        # Get initial transition count after first set
        initial_snapshot = get_governance_metrics().get_snapshot()
        initial_transitions = initial_snapshot["mode_transitions"]

        # Simulate detection of sensitive context
        context2 = {"request_context": ["medical"]}
        mode2 = select_mode(context2)
        assert mode2 == "cautious"
        set_governance_mode(mode2)

        # Simulate emergency trigger
        context3 = {"consecutive_rejections": 150}
        mode3 = select_mode(context3)
        assert mode3 == "emergency"
        set_governance_mode(mode3)

        # Verify transitions recorded (2 additional transitions from normal->cautious->emergency)
        summary = get_governance_summary()
        new_transitions = summary["mode_transitions"] - initial_transitions
        assert new_transitions == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
