# Experimental GPU-backed Memory (FractalPELMGPU)

## Status: EXPERIMENTAL

This module provides an optional GPU/CPU backend for phase-aware retrieval.
It is **not** part of the stable MLSDM API and is intended for research and
benchmarking purposes only.

## Overview

`FractalPELMGPU` is an experimental memory implementation that provides:

- GPU acceleration when CUDA is available (falls back to CPU)
- Batch operations for storing and retrieving vectors
- Phase-aware retrieval with configurable scoring

## Requirements

Requires PyTorch (not installed by default):

```bash
pip install mlsdm[neurolang]
# or directly:
pip install torch>=2.0.0
```

## API

The class is located in `mlsdm.memory.experimental`:

```python
from mlsdm.memory.experimental import FractalPELMGPU

# Create memory (auto-detects device: cuda if available, else cpu)
memory = FractalPELMGPU(
    dimension=384,      # Embedding dimension
    capacity=100_000,   # Maximum vectors to store
    device=None,        # "cuda", "cpu", or None for auto-detect
    use_amp=True,       # Automatic mixed precision (CUDA only)
    fractal_weight=0.3, # Distance weighting parameter
)

# Store vectors
memory.batch_entangle(vectors, phases, metadatas=None)

# Retrieve similar vectors
results = memory.retrieve(query_vector, current_phase, top_k=5)
# Returns: [(score, vector_np, metadata), ...]

# Batch retrieve
results = memory.batch_retrieve(query_vectors, current_phases, top_k=5)

# Reset memory
memory.reset()
```

## Scoring Formula

The retrieval score combines three factors:

```
score = cos_sim(q, v) × exp(-|φ_q - φ_v|) × clamp(1 - w × log1p(‖q - v‖), 0, 1)
```

Where:
- `cos_sim` — cosine similarity between query and stored vector
- `exp(-|Δφ|)` — phase similarity (peaks at 1.0 when phases match)
- `log1p(‖·‖)` — distance term with log for numerical stability
- `w` — `fractal_weight` parameter controlling distance influence

## Differences from Core PELM

| Aspect | PhaseEntangledLatticeMemory | FractalPELMGPU |
|--------|----------------------------|----------------|
| Location | `mlsdm.memory` | `mlsdm.memory.experimental` |
| Dependencies | numpy only | requires torch |
| Device | CPU only | CPU or GPU |
| Capacity | Ring buffer (overwrites) | Strict (raises error) |
| Storage | float32 | float16 vectors, float32 phases |
| Status | Production | Experimental |

## Benchmark

A benchmark script is available for manual testing:

```bash
python benchmarks/benchmark_fractal_pelm_gpu.py
```

This runs on CPU by default and compares with GPU if CUDA is available.

## Notes

- This module does **not** integrate with the core MLSDM pipeline
- The API may change in future versions without notice
- For production use, prefer `PhaseEntangledLatticeMemory` from `mlsdm.memory`
