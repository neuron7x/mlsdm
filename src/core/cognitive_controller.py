import numpy as np
import logging
from threading import Lock
from contextlib import contextmanager
from ..cognition.moral_filter_v2 import MoralFilterV2
from ..memory.qilm_v2 import QILM_v2
from ..rhythm.cognitive_rhythm import CognitiveRhythm
from ..memory.multi_level_memory import MultiLevelSynapticMemory

logger = logging.getLogger(__name__)


class LockTimeoutError(Exception):
    """Raised when lock acquisition times out."""
    pass

class CognitiveController:
    LOCK_TIMEOUT = 5.0  # seconds
    
    def __init__(self, dim=384):
        self.dim = dim
        self._lock = Lock()
        self.moral = MoralFilterV2(initial_threshold=0.50)
        self.qilm = QILM_v2(dimension=dim, capacity=20_000)
        self.rhythm = CognitiveRhythm(wake_duration=8, sleep_duration=3)
        self.synaptic = MultiLevelSynapticMemory(dimension=dim)
        self.step_counter = 0
        # Cache for phase values to avoid repeated computation
        self._phase_cache = {"wake": 0.1, "sleep": 0.9}
    
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

    def process_event(self, vector, moral_value):
        # Input validation
        if not isinstance(vector, np.ndarray):
            raise TypeError("vector must be a numpy.ndarray")
        
        if vector.shape[0] != self.dim:
            raise ValueError(f"vector dimension mismatch: expected {self.dim}, got {vector.shape[0]}")
        
        if np.any(np.isnan(vector)) or np.any(np.isinf(vector)):
            raise ValueError("vector contains NaN or Inf values")
        
        if not (0.0 <= moral_value <= 1.0):
            raise ValueError(f"moral_value must be in [0.0, 1.0], got {moral_value}")
        
        with self._acquire_lock():
            self.step_counter += 1
            accepted = self.moral.evaluate(moral_value)
            self.moral.adapt(accepted)
            if not accepted:
                return self._build_state(rejected=True, note="morally rejected")
            if not self.rhythm.is_wake():
                return self._build_state(rejected=True, note="sleep phase")
            self.synaptic.update(vector)
            # Optimize: use cached phase value
            phase_val = self._phase_cache[self.rhythm.phase]
            self.qilm.entangle(vector.tolist(), phase=phase_val)
            self.rhythm.step()
            return self._build_state(rejected=False, note="processed")

    def retrieve_context(self, query_vector, top_k=5):
        # Input validation
        if not isinstance(query_vector, np.ndarray):
            raise TypeError("query_vector must be a numpy.ndarray")
        
        if query_vector.shape[0] != self.dim:
            raise ValueError(f"query_vector dimension mismatch: expected {self.dim}, got {query_vector.shape[0]}")
        
        if np.any(np.isnan(query_vector)) or np.any(np.isinf(query_vector)):
            raise ValueError("query_vector contains NaN or Inf values")
        
        if not isinstance(top_k, int) or top_k < 1:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")
        
        with self._acquire_lock():
            # Optimize: use cached phase value
            phase_val = self._phase_cache[self.rhythm.phase]
            return self.qilm.retrieve(query_vector.tolist(), current_phase=phase_val, 
                                     phase_tolerance=0.15, top_k=top_k)

    def _build_state(self, rejected, note):
        l1, l2, l3 = self.synaptic.state()
        return {
            "step": self.step_counter,
            "phase": self.rhythm.phase,
            "moral_threshold": round(self.moral.threshold, 4),
            "moral_ema": round(self.moral.ema_accept_rate, 4),
            "synaptic_norms": {
                "L1": float(np.linalg.norm(l1)),
                "L2": float(np.linalg.norm(l2)),
                "L3": float(np.linalg.norm(l3))
            },
            "qilm_used": self.qilm.get_state_stats()["used"],
            "rejected": rejected,
            "note": note
        }
