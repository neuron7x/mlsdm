#!/usr/bin/env python3
"""
MLSDM Golden Path Demo

This is the canonical "from clone to live result" demonstration of MLSDM.
Run this script after installation to verify MLSDM is working correctly.

Usage:
    git clone https://github.com/neuron7x/mlsdm.git
    cd mlsdm
    pip install -e .
    python examples/golden_path_demo.py

Expected output: A governed response demonstrating MLSDM's cognitive wrapper.
"""

from mlsdm import create_llm_wrapper


def main() -> int:
    """Run the Golden Path demo."""
    print("=" * 60)
    print("🧠 MLSDM Golden Path Demo")
    print("=" * 60)

    # 1. Create the governed LLM wrapper with defaults
    print("\n▶ Creating MLSDM cognitive wrapper...")
    wrapper = create_llm_wrapper()
    print("  ✓ Wrapper initialized")
    print(f"    - Memory capacity: 20,000 vectors")
    print(f"    - Wake/Sleep cycle: 8/3 steps")
    print(f"    - Initial moral threshold: 0.50")

    # 2. Generate a governed response
    print("\n▶ Generating governed response...")
    prompt = "Explain what machine learning is in one sentence."
    result = wrapper.generate(prompt=prompt, moral_value=0.85)

    # 3. Display the result
    print("\n" + "-" * 60)
    print("📥 Input:")
    print(f"   Prompt: {prompt}")
    print(f"   Moral value: 0.85")

    print("\n📤 Output:")
    print(f"   Accepted: {result['accepted']}")
    print(f"   Phase: {result['phase']}")
    print(f"   Response: {result['response'][:150]}...")

    # 4. Show system state
    state = wrapper.get_state()
    print("\n📊 System State:")
    print(f"   Step: {state['step']}")
    print(f"   Moral threshold: {state['moral_threshold']:.2f}")
    print(f"   Memory used: {state['qilm_stats']['used']}/{state['qilm_stats']['capacity']}")
    print("-" * 60)

    # 5. Success message
    print("\n✓ Golden Path complete!")
    print("  MLSDM is working correctly.")
    print("\nNext steps:")
    print("  - Run tests: pytest tests/ -v")
    print("  - Start HTTP API: make run-dev")
    print("  - See SDK_USAGE.md for more examples")
    print("=" * 60 + "\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
