"""Experimental memory modules for MLSDM.

This package contains experimental and research-oriented memory implementations.
These modules are not part of the stable API and may change without notice.

EXPERIMENTAL STATUS:
- These implementations are for research and benchmarking purposes
- They require optional dependencies (torch) that are not installed by default
- They do not integrate with the core MLSDM pipeline
- API may change in future versions

Available modules:
- FractalPELMGPU: Optional GPU/CPU backend for phase-aware retrieval (requires torch)

Usage:
    try:
        from mlsdm.memory.experimental import FractalPELMGPU
    except ImportError as e:
        print(f"FractalPELMGPU requires torch: {e}")
"""

from __future__ import annotations

__all__: list[str] = []

# Lazy import - only export FractalPELMGPU if torch is available
try:
    from .fractal_pelm_gpu import FractalPELMGPU

    __all__.append("FractalPELMGPU")
except ImportError:
    # torch not available - FractalPELMGPU will not be exported
    # Users attempting to import it directly will get a clear error
    pass
