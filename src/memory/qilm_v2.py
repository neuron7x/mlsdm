import numpy as np
import logging
from typing import List, Optional
from dataclasses import dataclass
from threading import Lock
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class LockTimeoutError(Exception):
    """Raised when lock acquisition times out."""
    pass

@dataclass
class MemoryRetrieval:
    vector: np.ndarray
    phase: float
    resonance: float

class QILM_v2:
    LOCK_TIMEOUT = 5.0  # seconds
    
    def __init__(self, dimension: int = 384, capacity: int = 20000) -> None:
        self.dimension = dimension
        self.capacity = capacity
        self.pointer = 0
        self.size = 0
        self._lock = Lock()
        self.memory_bank = np.zeros((capacity, dimension), dtype=np.float32)
        self.phase_bank = np.zeros(capacity, dtype=np.float32)
        self.norms = np.zeros(capacity, dtype=np.float32)
    
    @contextmanager
    def _acquire_lock(self, timeout: float = None):
        """
        Context manager for lock acquisition with timeout.
        
        Args:
            timeout: Lock timeout in seconds (default: LOCK_TIMEOUT)
            
        Raises:
            LockTimeoutError: If lock cannot be acquired within timeout
        """
        if timeout is None:
            timeout = self.LOCK_TIMEOUT
        
        acquired = self._lock.acquire(timeout=timeout)
        if not acquired:
            raise LockTimeoutError(f"Failed to acquire lock within {timeout}s")
        
        try:
            yield
        finally:
            self._lock.release()

    def entangle(self, vector: List[float], phase: float) -> int:
        """
        Store a vector with phase information in memory.
        
        Args:
            vector: Input vector to store
            phase: Phase value (0.0-1.0)
            
        Returns:
            Index where vector was stored
            
        Raises:
            ValueError: If inputs are invalid
        """
        if not isinstance(vector, (list, np.ndarray)):
            raise TypeError("vector must be a list or numpy array")
        
        if not (0.0 <= phase <= 1.0):
            raise ValueError(f"phase must be in [0.0, 1.0], got {phase}")
        
        with self._acquire_lock():
            vec_np = np.array(vector, dtype=np.float32)
            
            if vec_np.shape[0] != self.dimension:
                raise ValueError(f"vector dimension mismatch: expected {self.dimension}, got {vec_np.shape[0]}")
            
            if np.any(np.isnan(vec_np)) or np.any(np.isinf(vec_np)):
                raise ValueError("vector contains NaN or Inf values")
            
            norm = float(np.linalg.norm(vec_np) or 1e-9)
            idx = self.pointer
            self.memory_bank[idx] = vec_np
            self.phase_bank[idx] = phase
            self.norms[idx] = norm
            self.pointer = (self.pointer + 1) % self.capacity
            self.size = min(self.size + 1, self.capacity)
            return idx

    def retrieve(self, query_vector: List[float], current_phase: float, phase_tolerance: float = 0.15, top_k: int = 5) -> List[MemoryRetrieval]:
        """
        Retrieve memories similar to query vector and phase.
        
        Args:
            query_vector: Query vector
            current_phase: Current phase (0.0-1.0)
            phase_tolerance: Phase matching tolerance
            top_k: Number of results to return
            
        Returns:
            List of MemoryRetrieval objects
            
        Raises:
            ValueError: If inputs are invalid
        """
        if not isinstance(query_vector, (list, np.ndarray)):
            raise TypeError("query_vector must be a list or numpy array")
        
        if not (0.0 <= current_phase <= 1.0):
            raise ValueError(f"current_phase must be in [0.0, 1.0], got {current_phase}")
        
        if not (0.0 <= phase_tolerance <= 1.0):
            raise ValueError(f"phase_tolerance must be in [0.0, 1.0], got {phase_tolerance}")
        
        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")
        
        with self._acquire_lock():
            if self.size == 0:
                return []
            q_vec = np.array(query_vector, dtype=np.float32)
            
            if q_vec.shape[0] != self.dimension:
                raise ValueError(f"query_vector dimension mismatch: expected {self.dimension}, got {q_vec.shape[0]}")
            
            if np.any(np.isnan(q_vec)) or np.any(np.isinf(q_vec)):
                raise ValueError("query_vector contains NaN or Inf values")
            
            q_norm = float(np.linalg.norm(q_vec))
            if q_norm < 1e-9:
                q_norm = 1e-9
            
            # Optimize: use in-place operations and avoid intermediate arrays
            phase_diff = np.abs(self.phase_bank[:self.size] - current_phase)
            phase_mask = phase_diff <= phase_tolerance
            if not np.any(phase_mask):
                return []
            
            candidates_idx = np.nonzero(phase_mask)[0]
            # Optimize: compute cosine similarity without intermediate array copies
            candidate_vectors = self.memory_bank[candidates_idx]
            candidate_norms = self.norms[candidates_idx]
            
            # Vectorized cosine similarity calculation
            cosine_sims = np.dot(candidate_vectors, q_vec) / (candidate_norms * q_norm)
            
            # Optimize: use argpartition only when beneficial (>2x top_k)
            num_candidates = len(cosine_sims)
            if num_candidates > top_k * 2:
                # Use partial sort for large result sets
                top_local = np.argpartition(cosine_sims, -top_k)[-top_k:]
                # Sort only the top k items
                top_local = top_local[np.argsort(cosine_sims[top_local])[::-1]]
            else:
                # Full sort for small result sets (faster for small arrays)
                top_local = np.argsort(cosine_sims)[::-1][:top_k]
            
            # Optimize: pre-allocate results list
            results: List[MemoryRetrieval] = []
            for loc in top_local:
                glob = candidates_idx[loc]
                results.append(MemoryRetrieval(
                    vector=self.memory_bank[glob],
                    phase=self.phase_bank[glob],
                    resonance=float(cosine_sims[loc])
                ))
            return results

    def get_state_stats(self) -> dict[str, int | float]:
        return {
            "capacity": self.capacity,
            "used": self.size,
            "memory_mb": round((self.memory_bank.nbytes + self.phase_bank.nbytes) / 1024**2, 2)
        }
