"""Memory subsystem for MLSDM.

Exports:
- PhaseEntangledLatticeMemory (PELM): Phase-entangled lattice memory
- MemoryRetrieval: Memory retrieval result dataclass
- QILM_v2: Deprecated alias for PhaseEntangledLatticeMemory (backward compatibility)
"""

from .phase_entangled_lattice_memory import (
    MemoryRetrieval,
    PhaseEntangledLatticeMemory,
)

# Backward compatibility (DEPRECATED - will be removed in v2.0.0)
# Use PhaseEntangledLatticeMemory instead
QILM_v2 = PhaseEntangledLatticeMemory

__all__ = [
    "PhaseEntangledLatticeMemory",
    "MemoryRetrieval",
    "QILM_v2",  # deprecated
]
