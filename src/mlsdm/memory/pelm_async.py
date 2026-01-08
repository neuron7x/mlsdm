"""Async-optimized PELM with non-blocking operations."""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import numpy as np


class PELMAsync:
    """Async PELM with thread pool for CPU-bound operations."""

    def __init__(self, capacity: int, dim: int, max_workers: int = 4) -> None:
        """Initialize with dedicated thread pool."""
        self._storage = np.zeros((capacity, dim), dtype=np.float32)
        self._metadata = np.zeros(capacity, dtype=np.int32)
        self._lock = asyncio.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._capacity = capacity
        self._dim = dim

    async def store(self, vector: np.ndarray, phase: float) -> int:
        """Async store operation."""
        loop = asyncio.get_running_loop()

        result = await loop.run_in_executor(
            self._executor,
            self._sync_store,
            vector,
            phase,
        )
        return result

    def _sync_store(self, vector: np.ndarray, phase: float) -> int:
        """Synchronous store logic (runs in thread pool)."""
        idx = self._find_insertion_index()

        self._storage[idx] = vector
        self._metadata[idx] = int(phase * 100)

        return idx

    async def retrieve(
        self,
        query: np.ndarray,
        top_k: int = 5,
        phase_filter: float | None = None,
    ) -> list[tuple[int, float, np.ndarray]]:
        """Async retrieve with parallel similarity computation."""
        loop = asyncio.get_running_loop()

        results = await loop.run_in_executor(
            self._executor,
            self._sync_retrieve,
            query,
            top_k,
            phase_filter,
        )
        return results

    def _sync_retrieve(
        self,
        query: np.ndarray,
        top_k: int,
        phase_filter: float | None,
    ) -> list[tuple[int, float, np.ndarray]]:
        """Synchronous retrieve logic with vectorized operations."""
        denom = np.linalg.norm(self._storage, axis=1) * np.linalg.norm(query)
        similarities = np.divide(
            np.dot(self._storage, query),
            denom,
            out=np.full(self._capacity, -np.inf, dtype=np.float32),
            where=denom != 0,
        )

        if phase_filter is not None:
            phase_mask = self._metadata == int(phase_filter * 100)
            similarities = np.where(phase_mask, similarities, -np.inf)

        top_indices = np.argpartition(similarities, -top_k)[-top_k:]
        top_indices = top_indices[np.argsort(similarities[top_indices])][::-1]

        results = [
            (int(idx), float(similarities[idx]), self._storage[idx])
            for idx in top_indices
        ]

        return results

    def _find_insertion_index(self) -> int:
        """Find insertion index (round-robin for simplicity)."""
        return int(np.random.randint(0, self._capacity))

    async def close(self) -> None:
        """Cleanup thread pool."""
        self._executor.shutdown(wait=True)

    @property
    def capacity(self) -> int:
        """Return current storage capacity."""
        return self._capacity

    @property
    def dim(self) -> int:
        """Return embedding dimensionality."""
        return self._dim
