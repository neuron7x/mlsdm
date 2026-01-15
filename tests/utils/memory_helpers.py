from __future__ import annotations

from datetime import datetime
from typing import Any

from mlsdm.memory.phase_entangled_lattice_memory import PhaseEntangledLatticeMemory
from mlsdm.memory.provenance import MemoryProvenance, MemorySource


def default_provenance(
    *,
    source: MemorySource = MemorySource.USER_INPUT,
    confidence: float = 0.9,
) -> MemoryProvenance:
    return MemoryProvenance(source=source, confidence=confidence, timestamp=datetime.now())


def entangle_with_provenance(
    memory: PhaseEntangledLatticeMemory,
    vector: list[float],
    phase: float,
    *,
    provenance: MemoryProvenance | None = None,
    **kwargs: Any,
) -> int:
    return memory.entangle(
        vector,
        phase,
        provenance=provenance or default_provenance(),
        **kwargs,
    )
