Architecture Spec (high level)

Core components:

- MultiLevelSynapticMemory
  - update(event_vector: np.ndarray) -> None
  - Maintains L1/L2/L3 states with decay + gated transfer.

- MoralFilter
  - evaluate(moral_value: float) -> bool
  - adapt(accept_rate: float) -> None
  - Adaptive threshold in [min_threshold, max_threshold].

- OntologyMatcher
  - match(event_vector: np.ndarray, metric: str = "cosine") -> (label, score)

- QILM
  - entangle_phase(event_vector: np.ndarray, phase: Any) -> None
  - retrieve(phase: Any, tolerance: float) -> List[np.ndarray]

- CognitiveRhythm
  - Discrete wake/sleep oscillation controlling processing.

- MemoryManager
  - Orchestrates memory, filter, matcher, QILM, rhythm and metrics.
  - async process_event(event_vector, moral_value).

- FastAPI API
  - /v1/process_event
  - /v1/state
  - /health
