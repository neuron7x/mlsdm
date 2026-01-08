"""Compare benchmark results and detect regressions."""
from __future__ import annotations

import argparse
import json
from typing import Any


def _load_benchmarks(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def compare_benchmarks(
    baseline_file: str,
    candidate_file: str,
    max_regression: float,
) -> bool:
    """Compare benchmark means and return True if within regression budget."""
    baseline = _load_benchmarks(baseline_file)
    candidate = _load_benchmarks(candidate_file)

    baseline_stats = {
        bench.get("name", ""): bench.get("stats", {}).get("mean", 0)
        for bench in baseline.get("benchmarks", [])
    }

    regressions: list[str] = []

    for bench in candidate.get("benchmarks", []):
        name = bench.get("name", "")
        candidate_mean = bench.get("stats", {}).get("mean", 0)
        if name not in baseline_stats:
            continue
        baseline_mean = baseline_stats[name]
        if baseline_mean == 0:
            continue
        delta = (candidate_mean - baseline_mean) / baseline_mean * 100
        if delta > max_regression:
            regressions.append(
                f"{name}: {delta:.2f}% regression (baseline {baseline_mean:.4f}, "
                f"candidate {candidate_mean:.4f})"
            )

    if regressions:
        print("❌ Benchmark regressions detected:")
        for regression in regressions:
            print(f"  - {regression}")
        return False

    print("✅ Benchmark regressions within tolerance")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare benchmark results.")
    parser.add_argument("baseline", help="Baseline benchmark JSON file")
    parser.add_argument("candidate", help="Candidate benchmark JSON file")
    parser.add_argument(
        "--max-regression",
        type=float,
        default=10.0,
        help="Maximum allowed regression percentage",
    )
    args = parser.parse_args()

    success = compare_benchmarks(args.baseline, args.candidate, args.max_regression)
    raise SystemExit(0 if success else 1)


if __name__ == "__main__":
    main()
