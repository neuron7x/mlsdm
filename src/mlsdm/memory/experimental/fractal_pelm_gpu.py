"""Experimental GPU-accelerated Phase-Entangled Lattice Memory backend.

This module provides a GPU-accelerated (via PyTorch) implementation for
phase-aware memory retrieval. It is experimental and not used in the
core MLSDM pipeline by default.

Requires: torch>=2.0.0 (install with 'pip install mlsdm[neurolang]')
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from contextlib import AbstractContextManager

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    # Provide None as placeholder when torch is not available
    torch = None  # type: ignore


class FractalPELMGPU:
    """Experimental GPU-accelerated backend for phase-aware memory retrieval.

    This class provides a GPU/torch-based implementation for storing and
    retrieving phase-entangled memory vectors. It uses fractal-weighted
    scoring that combines cosine similarity, phase similarity, and distance
    terms for relevance ranking.

    **Status**: Experimental - for research and benchmarks only.
    **Not used** in core MLSDM pipeline by default.

    The scoring function computes:
        score = cos_sim * phase_sim * clamp(1 - fractal_weight * dist_term, 0, 1)

    where:
        - cos_sim: cosine similarity between query and stored vectors
        - phase_sim: exp(-|Δφ|) for phase difference
        - dist_term: log1p(L2 distance) as fractal distance penalty

    Args:
        dimension: Embedding vector dimension (must be positive)
        capacity: Maximum number of vectors to store (must be positive)
        device: PyTorch device string ("cuda", "cpu", or None for auto-detect)
        use_amp: Whether to use automatic mixed precision (AMP) on CUDA
        fractal_weight: Weight for fractal distance penalty term in [0, 1]

    Raises:
        RuntimeError: If PyTorch is not installed
        ValueError: If dimension or capacity are not positive

    Example:
        >>> from mlsdm.memory.experimental import FractalPELMGPU
        >>> memory = FractalPELMGPU(dimension=384, capacity=10000, device="cpu")
        >>> vectors = np.random.randn(100, 384).astype(np.float32)
        >>> phases = np.random.uniform(0, 1, 100).astype(np.float32)
        >>> memory.batch_entangle(vectors, phases)
        >>> results = memory.retrieve(vectors[0], current_phase=0.5, top_k=5)
    """

    def __init__(
        self,
        dimension: int = 384,
        capacity: int = 100_000,
        device: str | None = None,
        use_amp: bool = True,
        fractal_weight: float = 0.3,
    ) -> None:
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "FractalPELMGPU requires PyTorch. "
                "Install with: pip install mlsdm[neurolang] or pip install torch>=2.0.0"
            )

        if dimension <= 0:
            raise ValueError(f"dimension must be positive, got {dimension}")
        if capacity <= 0:
            raise ValueError(f"capacity must be positive, got {capacity}")

        self.dimension = dimension
        self.capacity = capacity
        self.fractal_weight = fractal_weight

        # Auto-detect device if not specified
        if device is None:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self._device = torch.device(device)

        # AMP only makes sense on CUDA
        self.use_amp = use_amp and (self._device.type == "cuda")

        # Pre-allocate storage buffers
        self._vectors: torch.Tensor = torch.zeros(
            (capacity, dimension), dtype=torch.float16, device=self._device
        )
        self._phases: torch.Tensor = torch.zeros(capacity, dtype=torch.float32, device=self._device)
        self._norms: torch.Tensor = torch.zeros(capacity, dtype=torch.float32, device=self._device)
        self._metadata: list[dict[str, Any] | None] = [None] * capacity
        self.size: int = 0

    def _amp_context(self) -> AbstractContextManager[Any]:
        """Return autocast context manager for mixed precision.

        Returns AMP context with appropriate dtype for the device:
        - CUDA: enabled with bfloat16 (falls back to float16 if unsupported)
        - CPU: disabled (passthrough)
        """
        if self._device.type == "cuda" and self.use_amp:
            # Prefer bfloat16 if available, fall back to float16
            dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            return torch.autocast(device_type="cuda", enabled=True, dtype=dtype)
        return torch.autocast(device_type="cpu", enabled=False)

    def batch_entangle(
        self,
        vectors: np.ndarray[Any, np.dtype[np.floating[Any]]] | torch.Tensor,
        phases: np.ndarray[Any, np.dtype[np.floating[Any]]] | torch.Tensor,
        metadatas: list[dict[str, Any] | None] | None = None,
    ) -> None:
        """Store a batch of vectors with their phases and optional metadata.

        Args:
            vectors: Batch of vectors, shape (batch_size, dimension)
            phases: Phase values for each vector, shape (batch_size,)
            metadatas: Optional list of metadata dicts for each vector

        Raises:
            ValueError: If vector dimension doesn't match or shapes are inconsistent
            RuntimeError: If adding vectors would exceed capacity
        """
        # Convert numpy arrays to tensors if needed
        if isinstance(vectors, np.ndarray):
            vectors_t = torch.from_numpy(vectors).to(self._device)
        else:
            vectors_t = vectors.to(self._device)

        if isinstance(phases, np.ndarray):
            phases_t = torch.from_numpy(phases).to(self._device)
        else:
            phases_t = phases.to(self._device)

        # Validate shapes
        if vectors_t.ndim != 2:
            raise ValueError(f"vectors must be 2D, got shape {vectors_t.shape}")
        batch_size, dim = vectors_t.shape
        if dim != self.dimension:
            raise ValueError(f"vector dimension mismatch: expected {self.dimension}, got {dim}")
        if phases_t.shape[0] != batch_size:
            raise ValueError(
                f"phases batch size mismatch: expected {batch_size}, got {phases_t.shape[0]}"
            )

        # Check capacity
        if self.size + batch_size > self.capacity:
            raise RuntimeError(
                f"Capacity exceeded: cannot add {batch_size} vectors "
                f"(current: {self.size}, capacity: {self.capacity})"
            )

        # Compute norms
        norms = torch.linalg.norm(vectors_t.float(), dim=1)
        # Avoid division by zero
        norms = torch.clamp(norms, min=1e-9)

        # Store in buffers
        start_idx = self.size
        end_idx = self.size + batch_size
        self._vectors[start_idx:end_idx] = vectors_t.half()
        self._phases[start_idx:end_idx] = phases_t.float()
        self._norms[start_idx:end_idx] = norms

        # Store metadata
        if metadatas is not None:
            if len(metadatas) != batch_size:
                raise ValueError(
                    f"metadatas length mismatch: expected {batch_size}, got {len(metadatas)}"
                )
            for i, meta in enumerate(metadatas):
                self._metadata[start_idx + i] = meta

        self.size += batch_size

    def _score_single(self, query_vec: torch.Tensor, query_phase: float) -> torch.Tensor:
        """Compute relevance scores for a single query.

        Args:
            query_vec: Query vector, shape (dimension,)
            query_phase: Current phase value

        Returns:
            Tensor of scores, shape (size,), or empty tensor if size == 0
        """
        if self.size == 0:
            return torch.tensor([], device=self._device)

        with self._amp_context():
            # Get active portion of buffers
            active_vectors = self._vectors[: self.size].float()
            active_norms = self._norms[: self.size]
            active_phases = self._phases[: self.size]

            # Query norm
            query_vec_f = query_vec.float()
            query_norm = torch.linalg.norm(query_vec_f)
            query_norm = torch.clamp(query_norm, min=1e-9)

            # Cosine similarity: dot(q, v) / (||q|| * ||v||)
            dots = torch.mv(active_vectors, query_vec_f)
            cos_sim = dots / (query_norm * active_norms)

            # Phase similarity: exp(-|Δφ|)
            phase_diff = torch.abs(active_phases - query_phase)
            phase_sim = torch.exp(-phase_diff)

            # Fractal distance term: log1p(L2 distance)
            # Compute L2 distances using cdist for efficiency
            query_2d = query_vec_f.unsqueeze(0)  # (1, dim)
            distances = torch.cdist(query_2d, active_vectors, p=2).squeeze(0)  # (size,)
            dist_term = torch.log1p(distances)

            # Combined score with fractal weighting
            fractal_factor = torch.clamp(1.0 - self.fractal_weight * dist_term, min=0.0, max=1.0)
            scores = cos_sim * phase_sim * fractal_factor

        return scores

    def retrieve(
        self,
        query_vector: np.ndarray[Any, np.dtype[np.floating[Any]]] | torch.Tensor,
        current_phase: float,
        top_k: int = 5,
    ) -> list[tuple[float, np.ndarray[Any, np.dtype[np.float32]], dict[str, Any] | None]]:
        """Retrieve top-k most relevant vectors for a query.

        Args:
            query_vector: Query vector, shape (dimension,)
            current_phase: Current phase value for phase-aware retrieval
            top_k: Number of results to return

        Returns:
            List of tuples: (score, vector_np, metadata)
            - score: float relevance score
            - vector_np: numpy array of shape (dimension,) with dtype float32
            - metadata: optional dict or None

        Raises:
            ValueError: If query_vector shape doesn't match dimension
        """
        # Convert to tensor if needed
        if isinstance(query_vector, np.ndarray):
            query_t = torch.from_numpy(query_vector).to(self._device)
        else:
            query_t = query_vector.to(self._device)

        # Validate shape
        if query_t.shape != (self.dimension,):
            raise ValueError(
                f"query_vector shape mismatch: expected ({self.dimension},), got {query_t.shape}"
            )

        if self.size == 0:
            return []

        # Compute scores
        scores = self._score_single(query_t, current_phase)

        # Get top-k indices
        k = min(top_k, self.size)
        top_scores, top_indices = torch.topk(scores, k)

        # Build results
        results: list[tuple[float, np.ndarray[Any, np.dtype[np.float32]], dict[str, Any] | None]] = (
            []
        )
        for i in range(k):
            idx = int(top_indices[i].item())
            score = float(top_scores[i].item())
            vector_np = self._vectors[idx].float().cpu().numpy().astype(np.float32)
            metadata = self._metadata[idx]
            results.append((score, vector_np, metadata))

        return results

    def batch_retrieve(
        self,
        query_vectors: np.ndarray[Any, np.dtype[np.floating[Any]]] | torch.Tensor,
        current_phases: np.ndarray[Any, np.dtype[np.floating[Any]]] | torch.Tensor,
        top_k: int = 5,
    ) -> list[list[tuple[float, np.ndarray[Any, np.dtype[np.float32]], dict[str, Any] | None]]]:
        """Batch retrieve top-k vectors for multiple queries.

        Args:
            query_vectors: Batch of query vectors, shape (batch_size, dimension)
            current_phases: Phase values for each query, shape (batch_size,)
            top_k: Number of results to return per query

        Returns:
            List of lists, one per query, each containing tuples:
            (score, vector_np, metadata)

        Raises:
            ValueError: If shapes are inconsistent
        """
        # Convert to tensors if needed
        if isinstance(query_vectors, np.ndarray):
            queries_t = torch.from_numpy(query_vectors).to(self._device)
        else:
            queries_t = query_vectors.to(self._device)

        if isinstance(current_phases, np.ndarray):
            phases_t = torch.from_numpy(current_phases).to(self._device)
        else:
            phases_t = current_phases.to(self._device)

        # Validate shapes
        if queries_t.ndim != 2:
            raise ValueError(f"query_vectors must be 2D, got shape {queries_t.shape}")
        batch_size, dim = queries_t.shape
        if dim != self.dimension:
            raise ValueError(f"vector dimension mismatch: expected {self.dimension}, got {dim}")
        if phases_t.shape[0] != batch_size:
            raise ValueError(
                f"phases batch size mismatch: expected {batch_size}, got {phases_t.shape[0]}"
            )

        # Process each query
        all_results: list[
            list[tuple[float, np.ndarray[Any, np.dtype[np.float32]], dict[str, Any] | None]]
        ] = []
        for i in range(batch_size):
            query_vec = queries_t[i]
            phase = float(phases_t[i].item())
            results = self.retrieve(query_vec, phase, top_k)
            all_results.append(results)

        return all_results

    def reset(self) -> None:
        """Clear all stored vectors while preserving capacity.

        This resets the memory to an empty state without reallocating buffers.
        """
        self.size = 0
        # Reset metadata list
        self._metadata = [None] * self.capacity
        # Optionally zero out tensors (not strictly necessary but clean)
        self._vectors.zero_()
        self._phases.zero_()
        self._norms.zero_()
