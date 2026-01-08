"""Complete performance profiling for /generate endpoint."""
from __future__ import annotations

import cProfile
import io
import pstats

from fastapi.testclient import TestClient

from mlsdm.api.app import app


def profile_generate_endpoint() -> None:
    """Profile complete /generate call with detailed breakdown."""
    client = TestClient(app)

    profiler = cProfile.Profile()
    profiler.enable()

    # Run 100 requests to get statistical significance
    for i in range(100):
        client.post(
            "/generate",
            json={
                "prompt": f"Test prompt {i}",
                "max_tokens": 50,
                "moral_value": 0.8,
            },
        )

    profiler.disable()

    # Output results
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream).sort_stats("cumulative")
    stats.print_stats(50)  # Top 50 functions

    with open("profiling_results.txt", "w", encoding="utf-8") as handle:
        handle.write(stream.getvalue())

    print(stream.getvalue())


if __name__ == "__main__":
    profile_generate_endpoint()
