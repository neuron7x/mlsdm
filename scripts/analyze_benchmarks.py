"""Analyze benchmark results and enforce gates."""
from __future__ import annotations

import json
import sys


def analyze_benchmarks(results_file: str) -> bool:
    """Analyze benchmark results and return True if passing."""
    with open(results_file, encoding="utf-8") as handle:
        data = json.load(handle)

    failures: list[str] = []

    for benchmark in data.get("benchmarks", []):
        name = benchmark.get("name", "")
        stats = benchmark.get("stats", {})

        if "p50" in name and stats.get("mean", 0) > 0.030:
            failures.append(f"{name}: P50 {stats['mean']*1000:.2f}ms > 30ms")

        if "p95" in name and stats.get("mean", 0) > 0.120:
            failures.append(f"{name}: P95 {stats['mean']*1000:.2f}ms > 120ms")

        if "p99" in name and stats.get("mean", 0) > 0.200:
            failures.append(f"{name}: P99 {stats['mean']*1000:.2f}ms > 200ms")

        if "throughput" in name and stats.get("mean", 0) < 100:
            failures.append(f"{name}: Throughput {stats['mean']:.2f} RPS < 100 RPS")

    if failures:
        print("❌ Performance gates FAILED:")
        for failure in failures:
            print(f"  - {failure}")
        return False

    print("✅ All performance gates PASSED")
    return True


if __name__ == "__main__":
    success = analyze_benchmarks(sys.argv[1])
    sys.exit(0 if success else 1)
