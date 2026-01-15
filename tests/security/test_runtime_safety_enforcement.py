"""Runtime safety enforcement tests for drift, memory integrity, and boundary hits."""

from __future__ import annotations

from datetime import datetime

import pytest

from mlsdm.cognition.moral_filter_v2 import MoralFilterV2
from mlsdm.memory.phase_entangled_lattice_memory import PhaseEntangledLatticeMemory
from mlsdm.memory.provenance import MemoryProvenance, MemorySource
from mlsdm.observability.safety_boundary_tracker import reset_safety_boundary_tracker
from mlsdm.security import guardrails


def test_policy_drift_lockdown_triggers_on_critical_drift() -> None:
    filter_instance = MoralFilterV2(initial_threshold=0.5, filter_id="test")
    filter_instance._DRIFT_CRITICAL_THRESHOLD = 0.01

    filter_instance.adapt(accepted=True)
    filter_instance.adapt(accepted=True)

    assert filter_instance._drift_lockdown is True
    assert filter_instance.threshold == filter_instance.MAX_THRESHOLD

    locked_threshold = filter_instance.threshold
    filter_instance.adapt(accepted=False)
    assert filter_instance.threshold == locked_threshold


def test_low_confidence_llm_memory_rejected() -> None:
    memory = PhaseEntangledLatticeMemory(dimension=2, capacity=8)
    provenance = MemoryProvenance(
        source=MemorySource.LLM_GENERATION,
        confidence=0.6,
        timestamp=datetime.now(),
    )
    idx = memory.entangle([0.1, 0.2], 0.5, provenance=provenance)

    assert idx == -1
    assert memory.size == 0


def test_retrieval_filters_low_confidence_llm_memory() -> None:
    memory = PhaseEntangledLatticeMemory(dimension=2, capacity=8)
    provenance = MemoryProvenance(
        source=MemorySource.LLM_GENERATION,
        confidence=0.8,
        timestamp=datetime.now(),
    )
    idx = memory.entangle([1.0, 0.0], 0.5, provenance=provenance)
    assert idx != -1

    memory._provenance[0] = MemoryProvenance(
        source=MemorySource.LLM_GENERATION,
        confidence=0.4,
        timestamp=datetime.now(),
    )

    results = memory.retrieve([1.0, 0.0], current_phase=0.5, top_k=1, min_confidence=0.0)
    assert results == []


@pytest.mark.asyncio
async def test_safety_boundary_quarantine_on_repeated_denials(monkeypatch: pytest.MonkeyPatch) -> None:
    reset_safety_boundary_tracker()

    async def _deny_auth(_: guardrails.GuardrailContext) -> guardrails.GuardrailResult:
        return guardrails.GuardrailResult(
            check_type=guardrails.GuardrailCheckType.AUTHENTICATION,
            passed=False,
            reason="auth_failed",
            stride_category=guardrails.StrideCategory.SPOOFING,
        )

    async def _allow_check(_: guardrails.GuardrailContext) -> guardrails.GuardrailResult:
        return guardrails.GuardrailResult(
            check_type=guardrails.GuardrailCheckType.REQUEST_SIGNING,
            passed=True,
            stride_category=guardrails.StrideCategory.TAMPERING,
        )

    async def _allow_rate(_: guardrails.GuardrailContext) -> guardrails.GuardrailResult:
        return guardrails.GuardrailResult(
            check_type=guardrails.GuardrailCheckType.RATE_LIMITING,
            passed=True,
            stride_category=guardrails.StrideCategory.DENIAL_OF_SERVICE,
        )

    async def _allow_pii(_: guardrails.GuardrailContext) -> guardrails.GuardrailResult:
        return guardrails.GuardrailResult(
            check_type=guardrails.GuardrailCheckType.PII_SCRUBBING,
            passed=True,
            stride_category=guardrails.StrideCategory.INFORMATION_DISCLOSURE,
        )

    monkeypatch.setattr(guardrails, "_check_authentication", _deny_auth)
    monkeypatch.setattr(guardrails, "_check_request_signing", _allow_check)
    monkeypatch.setattr(guardrails, "_check_rate_limiting", _allow_rate)
    monkeypatch.setattr(guardrails, "_check_pii_scrubbing", _allow_pii)

    context = guardrails.GuardrailContext(route="/generate", client_id="client-1")

    for _ in range(2):
        decision = await guardrails.enforce_request_guardrails(context)
        assert "safety_boundary_quarantine" not in decision["reasons"]

    decision = await guardrails.enforce_request_guardrails(context)
    assert decision["allow"] is False
    assert "safety_boundary_quarantine" in decision["reasons"]
    assert decision["metadata"]["safety_boundary"]["action"] == "quarantine"
