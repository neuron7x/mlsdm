"""Experimental memory backends for MLSDM.

This module contains experimental GPU-accelerated memory implementations
that are NOT used in the core MLSDM pipeline by default.

These backends are intended for research, benchmarks, and specialized use cases.
They require optional PyTorch dependencies ('mlsdm[neurolang]').

Available experimental backends:
- FractalPELMGPU: GPU-accelerated phase-entangled memory for high-throughput retrieval

Usage:
    from mlsdm.memory.experimental import FractalPELMGPU

    # Create GPU backend (falls back to CPU if CUDA unavailable)
    memory = FractalPELMGPU(dimension=384, capacity=100_000)
"""

from __future__ import annotations

__all__: list[str] = []

try:
    from .fractal_pelm_gpu import FractalPELMGPU

    __all__ = ["FractalPELMGPU"]
except ImportError:
    # PyTorch not installed - experimental backends unavailable
    pass
