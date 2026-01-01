# Neuro-AI Functional Contracts

Version: 1.0  
Status: Draft (backwards-compatible)

This document formalizes the functional contracts for biomimetic components in MLSDM. Each contract is explicitly testable and backed by source paths.

## Modules

### MultiLevelSynapticMemory (`src/mlsdm/memory/multi_level_memory.py`)
- **Role (computational)**: Multi-timescale synaptic buffer (L1/L2/L3) with gated consolidation.
- **Inputs**: `event: np.ndarray[dim]`, decay rates `λ1/λ2/λ3`, thresholds `θ1/θ2`, gating `g12/g23`, optional `correlation_id`.
- **Outputs**: Updated L1/L2/L3 traces, consolidation flags (via observability hook), memory usage estimate.
- **Constraints**: `0<λ<=1`, `θ>0`, `0<=g<=1`, no NaN/inf, dimension must match. Updates must be bounded (decay before add).
- **Failure / fallback**: Reject invalid shapes with `ValueError`; if calibration unavailable, use safe defaults and zeroed traces.
- **Hybrid improvement**: Bounded decay and gating, observability metrics (`record_synaptic_update`), deterministic in-place updates for testability.

### PhaseEntangledLatticeMemory (`src/mlsdm/memory/phase_entangled_lattice_memory.py`)
- **Role**: Phase-coded associative memory (bidirectional retrieval).
- **Inputs**: Keys/values embeddings, phase weights, similarity thresholds, capacity bound.
- **Outputs**: Top-k results with phase coherence, eviction decisions.
- **Constraints**: Capacity hard limit, similarity threshold prevents degenerate matches, no NaN phases.
- **Failure / fallback**: Empty result set when below threshold; prior state unchanged on invalid phase input.
- **Hybrid improvement**: Deterministic eviction ordering, bounded similarity thresholds for stability.

### CognitiveRhythm (`src/mlsdm/rhythm/cognitive_rhythm.py`)
- **Role**: Wake/sleep pacing for consolidation and replay.
- **Inputs**: `wake_duration`, `sleep_duration`, `step()` ticks, optional risk modulation.
- **Outputs**: `phase` (`wake|sleep`), `counter`, convenience `is_wake/is_sleep`.
- **Constraints**: Durations > 0; transitions bounded by hysteresis/cooldown when regime control is enabled.
- **Failure / fallback**: Stays in last stable phase if durations invalid; counter resets on transition.
- **Hybrid improvement**: Boolean fast-path checks; optional regime-aware tau scaling for defensive mode.

### SynergyExperienceMemory (`src/mlsdm/cognition/synergy_experience.py`)
- **Role**: Prediction-error-driven combo selection with ε-greedy balance.
- **Inputs**: `state_signature`, `combo_id`, `delta_eoi`, `epsilon`, EMA smoothing factor.
- **Outputs**: `ComboStats` (attempts, mean/EMA Δeoi), exploration/exploitation counts.
- **Constraints**: `epsilon in [0,1]`, sanitized Δeoi (no NaN/inf), bounded EMA α.
- **Failure / fallback**: Neutral stats before `min_trials_for_confidence`; exploration fallback when stats missing.
- **Hybrid improvement**: Thread-safe updates, bounded EMA for stability, explicit Δ-driven learning (not reward-only).

## Contract Guardrails
- **Prediction-error first**: Adaptation uses Δ = observed − predicted (see `PredictionErrorAdapter`).
- **Risk-driven dynamics**: Threat/risk modulates inhibition gain, exploration rate, and tau scaling via `RegimeController`.
- **Stability**: Bounded updates, hysteresis, cooldown, and clipping prevent oscillations.
- **Observability**: Metrics exposed via adapters (`NeuroAIStepMetrics`) and existing telemetry hooks.
