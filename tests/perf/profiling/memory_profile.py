"""Memory usage profiling."""
from __future__ import annotations

from fastapi.testclient import TestClient
from memory_profiler import profile

from mlsdm.api.app import app


@profile
def memory_test_generate() -> None:
    """Run memory profiling against /generate."""
    client = TestClient(app)

    for i in range(50):
        client.post(
            "/generate",
            json={
                "prompt": f"Memory test {i}",
                "max_tokens": 50,
                "moral_value": 0.8,
            },
        )

        if i % 10 == 0:
            print(f"Completed {i} requests")


if __name__ == "__main__":
    memory_test_generate()
