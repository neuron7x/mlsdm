"""
Neuro-AI contract layer adapters.

This package adds a thin compatibility layer that formalizes the computational
contracts of biomimetic modules (synaptic memory, cognitive rhythm, and
synergy learning) while keeping the default behavior untouched.

The adapters are opt-in: when disabled they delegate directly to the existing
implementations, ensuring no breaking changes to public APIs.
"""

from .adapters import (
    NeuroAIStepMetrics,
    PredictionErrorAdapter,
    PredictionErrorMetrics,
    RegimeController,
    RegimeDecision,
    RegimeState,
    SynapticMemoryAdapter,
)
from .contracts import NEURO_CONTRACTS, ContractSpec

__all__ = [
    "ContractSpec",
    "NEURO_CONTRACTS",
    "NeuroAIStepMetrics",
    "PredictionErrorAdapter",
    "PredictionErrorMetrics",
    "RegimeController",
    "RegimeDecision",
    "RegimeState",
    "SynapticMemoryAdapter",
]
