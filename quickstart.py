#!/usr/bin/env python3
"""
MLSDM Governed Cognitive Memory - Quickstart Demo

This script demonstrates the basic usage of the library.
Run this after installation to verify everything works.
"""

import numpy as np
from src.core.llm_wrapper import LLMWrapper


def mock_llm(prompt: str, max_tokens: int) -> str:
    """Mock LLM for demonstration - replace with your actual LLM."""
    return f"Response to: {prompt[:50]}..."


def mock_embedder(text: str) -> np.ndarray:
    """Mock embedder for demonstration - replace with your actual embedding model."""
    # In production, use sentence-transformers, OpenAI embeddings, etc.
    return np.random.randn(384).astype(np.float32)


def main():
    print("=" * 70)
    print("MLSDM Governed Cognitive Memory - Quickstart Demo")
    print("=" * 70)
    print()

    # Step 1: Create wrapper
    print("Step 1: Creating LLM wrapper with cognitive governance...")
    wrapper = LLMWrapper(
        llm_generate_fn=mock_llm,
        embedding_fn=mock_embedder,
        dim=384,
        capacity=20_000,
        wake_duration=8,
        sleep_duration=3,
        initial_moral_threshold=0.50,
    )
    print("✓ Wrapper created successfully")
    print()

    # Step 2: Test acceptable request
    print("Step 2: Testing acceptable request (moral_value=0.8)...")
    result = wrapper.generate(
        prompt="Hello, how can I help you today?", moral_value=0.8
    )
    print(f"  Response: {result['response']}")
    print(f"  Accepted: {result['accepted']}")
    print(f"  Phase: {result['phase']}")
    print(f"  Moral Threshold: {result['moral_threshold']:.2f}")
    print()

    # Step 3: Test low moral value request
    print("Step 3: Testing low moral value request (moral_value=0.2)...")
    result = wrapper.generate(
        prompt="Tell me something harmful", moral_value=0.2
    )
    print(f"  Response: {result['response']}")
    print(f"  Accepted: {result['accepted']}")
    print(f"  Note: {result['note']}")
    print()

    # Step 4: Cycle through phases
    print("Step 4: Cycling through cognitive phases...")
    for i in range(12):
        result = wrapper.generate(
            prompt=f"Request {i}", moral_value=0.7
        )
        if i == 0 or i == 8:
            print(f"  Step {i}: Phase={result['phase']}, Threshold={result['moral_threshold']:.2f}")
    print()

    # Step 5: Direct cognitive controller access
    print("Step 5: Testing low-level CognitiveController...")
    from src.core.cognitive_controller import CognitiveController

    controller = CognitiveController(dim=384)
    vector = np.random.randn(384).astype(np.float32)
    vector = vector / np.linalg.norm(vector)

    state = controller.process_event(vector, moral_value=0.85)
    print(f"  State: {state}")
    print()

    print("=" * 70)
    print("✓ Quickstart completed successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Replace mock_llm with your actual LLM (OpenAI, Anthropic, etc.)")
    print("  2. Replace mock_embedder with your embedding model")
    print("  3. See examples/ directory for production examples")
    print("  4. Read USAGE_GUIDE.md for detailed documentation")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
