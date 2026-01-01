"""
Functional contracts for biomimetic modules.

These contracts are lightweight, testable descriptions that capture the
computational role, inputs/outputs, safety constraints, and fallback modes for
each neuro-inspired component. They are used by the Neuro-AI adapters and the
documentation in docs/neuro_ai/CONTRACTS.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


@dataclass(frozen=True)
class ContractSpec:
    """Declarative contract for a biomimetic module."""

    name: str
    role: str
    inputs: Sequence[str]
    outputs: Sequence[str]
    constraints: Sequence[str]
    failure_modes: Sequence[str]
    hybrid_improvements: Sequence[str]
    references: Sequence[str]


# Canonical contracts used by docs and tests
NEURO_CONTRACTS: Mapping[str, ContractSpec] = {
    "MultiLevelSynapticMemory": ContractSpec(
        name="MultiLevelSynapticMemory",
        role="Multi-timescale synaptic buffer and consolidation gate",
        inputs=[
            "event: np.ndarray",
            "lambda_l1/l2/l3 decay rates",
            "theta_l1/theta_l2 consolidation thresholds",
        ],
        outputs=["updated L1/L2/L3 traces", "consolidation flags"],
        constraints=[
            "Decay rates in (0,1], thresholds > 0",
            "No NaNs/inf in traces",
            "Memory usage must stay bounded by dimension",
        ],
        failure_modes=[
            "Fallback to zeroed traces on invalid input shape",
            "No consolidation when thresholds are not met",
        ],
        hybrid_improvements=[
            "Observability hook for latency and consolidation",
            "Bounded decay and gating to prevent runaway growth",
        ],
        references=[
            "src/mlsdm/memory/multi_level_memory.py",
            "docs/NEURO_FOUNDATIONS.md#multi-timescale-synaptic-memory",
        ],
    ),
    "PhaseEntangledLatticeMemory": ContractSpec(
        name="PhaseEntangledLatticeMemory",
        role="Phase-coded associative memory for bidirectional retrieval",
        inputs=[
            "keys/values embeddings",
            "phase weights for associative retrieval",
        ],
        outputs=["top-k associative results", "phase coherence score"],
        constraints=[
            "Capacity bound respected via eviction policy",
            "Similarity thresholds avoid degenerate matches",
        ],
        failure_modes=[
            "Returns empty result when similarity below threshold",
            "Keeps prior state unchanged on invalid phase input",
        ],
        hybrid_improvements=[
            "Deterministic eviction ordering for testability",
            "Bounded similarity thresholds to avoid oscillations",
        ],
        references=[
            "src/mlsdm/memory/phase_entangled_lattice_memory.py",
            "docs/NEURO_FOUNDATIONS.md#phase-entangled-lattice-memory-pelm",
        ],
    ),
    "CognitiveRhythm": ContractSpec(
        name="CognitiveRhythm",
        role="Wake/sleep phase pacing with regime-aware time constants",
        inputs=["wake_duration", "sleep_duration", "step() ticks", "optional risk signal"],
        outputs=["current phase label", "phase counter"],
        constraints=[
            "Durations must be positive",
            "Phase transitions bounded by hysteresis/cooldown",
        ],
        failure_modes=[
            "Stays in last stable phase if invalid duration provided",
            "Counter resets to duration on transition",
        ],
        hybrid_improvements=[
            "Boolean fast-path for hot checks (is_wake/is_sleep)",
            "Optional regime modulation for faster defensive adaptation",
        ],
        references=[
            "src/mlsdm/rhythm/cognitive_rhythm.py",
            "docs/NEURO_FOUNDATIONS.md#circadian-rhythms-and-sleep",
        ],
    ),
    "SynergyExperienceMemory": ContractSpec(
        name="SynergyExperienceMemory",
        role="Prediction-error-driven combo selection with ε-greedy balance",
        inputs=[
            "state_signature",
            "combo_id",
            "delta_eoi (observed-predicted objective index)",
            "epsilon exploration rate",
        ],
        outputs=["ComboStats (ema_delta_eoi, attempts, mean_delta_eoi)", "selected combo id"],
        constraints=[
            "epsilon in [0,1]",
            "delta_eoi sanitized to avoid NaN/inf",
            "bounded EMA smoothing factor",
        ],
        failure_modes=[
            "Defaults to neutral stats when insufficient trials",
            "Falls back to exploration when no stats exist",
        ],
        hybrid_improvements=[
            "Thread-safe updates via locks",
            "EMA smoothing for stability under noisy deltas",
        ],
        references=[
            "src/mlsdm/cognition/synergy_experience.py",
            "tests/unit/test_synergy_experience.py",
        ],
    ),
}
