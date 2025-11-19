from __future__ import annotations
from typing import List, Any
import numpy as np
from numpy.typing import NDArray

class QILM:
    def __init__(self, dimension: int):
        self.dim = dimension
        self.memory: List[NDArray[Any]] = []
        self.phases: List[float] = []

    def entangle(self, vector: NDArray[Any], phase: float | None = None) -> None:
        if vector.shape != (self.dim,):
            raise ValueError("Vector dimension mismatch")
        self.memory.append(vector.astype(np.float32).copy())
        self.phases.append(phase if phase is not None else np.random.rand())

    def retrieve(self, phase: float, tolerance: float = 0.12) -> List[NDArray[Any]]:
        return [
            vec for vec, ph in zip(self.memory, self.phases)
            if abs(ph - phase) <= tolerance
        ]
    
    def __len__(self) -> int:
        return len(self.memory)
