"""Async NeuroCognitiveEngine."""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import numpy as np

from mlsdm.cognition.moral_filter_v3 import MoralFilterV3
from mlsdm.memory.pelm_async import PELMAsync

if TYPE_CHECKING:
    from mlsdm.engine.neuro_cognitive_engine import NeuroEngineConfig


class NeuroCognitiveEngineAsync:
    """Fully async engine implementation."""

    def __init__(self, config: NeuroEngineConfig) -> None:
        self.pelm = PELMAsync(
            capacity=config.pelm_capacity,
            dim=config.dim,
            max_workers=config.worker_threads or 4,
        )
        self.moral_filter = MoralFilterV3(enable_fast_path=True)

    async def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Async generate with parallel operations."""
        embedding = await self._embed_prompt(prompt)
        context = await self.pelm.retrieve(embedding, top_k=5)

        moral_score = float(kwargs.get("moral_value", 0.5))
        decision = self.moral_filter.filter(moral_score)

        if not decision.accepted:
            return {
                "response": "",
                "accepted": False,
                "rejected_at": "moral_filter",
                "moral_score": moral_score,
            }

        response = await self._generate_llm(prompt, context)

        return {
            "response": response,
            "accepted": True,
            "moral_score": moral_score,
            "phase": "wake",
        }

    async def _embed_prompt(self, prompt: str) -> np.ndarray:
        """Async prompt embedding."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_embed, prompt)

    def _sync_embed(self, prompt: str) -> np.ndarray:
        """Synchronous embedding logic."""
        _ = prompt
        return np.random.randn(384).astype(np.float32)

    async def _generate_llm(self, prompt: str, context: list[Any]) -> str:
        """Async LLM generation."""
        _ = context
        return f"Generated response for: {prompt}"

    async def close(self) -> None:
        """Cleanup async resources."""
        await self.pelm.close()
