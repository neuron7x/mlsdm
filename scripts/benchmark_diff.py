#!/usr/bin/env python3
import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BenchmarkSummary:
    max_median_p95_ms: float
    samples: int


def parse_benchmark_output(path: Path) -> BenchmarkSummary:
    content = path.read_text(encoding="utf-8", errors="ignore")
    matches = re.findall(r"Median P95[^0-9]*([0-9.]+)ms", content)
    if not matches:
        raise ValueError(f"No median P95 values found in {path}")
    values = [float(value) for value in matches]
    return BenchmarkSummary(max_median_p95_ms=max(values), samples=len(values))


def compare_baseline(
    baseline: BenchmarkSummary,
    current: BenchmarkSummary,
    threshold: float,
) -> tuple[bool, str]:
    allowed = baseline.max_median_p95_ms * (1 + threshold)
    passed = current.max_median_p95_ms <= allowed
    status = "✅" if passed else "❌"
    details = (
        f"{status} Max median P95: {current.max_median_p95_ms:.3f}ms "
        f"(baseline {baseline.max_median_p95_ms:.3f}ms, "
        f"allowed {allowed:.3f}ms, threshold {threshold:.0%})"
    )
    return passed, details


def render_markdown(
    baseline: BenchmarkSummary,
    current: BenchmarkSummary,
    threshold: float,
    comparison: str,
) -> str:
    return "\n".join(
        [
            "## Benchmark Comparison",
            "",
            "| Metric | Baseline | PR |",
            "| --- | --- | --- |",
            (
                f"| Max median P95 (ms) | {baseline.max_median_p95_ms:.3f} "
                f"({baseline.samples} samples) | {current.max_median_p95_ms:.3f} "
                f"({current.samples} samples) |"
            ),
            "",
            f"Threshold: {threshold:.0%}",
            comparison,
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare benchmark outputs")
    parser.add_argument("baseline", type=Path, help="Baseline benchmark output")
    parser.add_argument("current", type=Path, help="Current benchmark output")
    parser.add_argument("--threshold", type=float, default=0.1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        baseline_summary = parse_benchmark_output(args.baseline)
        current_summary = parse_benchmark_output(args.current)
    except Exception as exc:
        print(f"❌ Failed to parse benchmark outputs: {exc}")
        return 1

    passed, comparison = compare_baseline(
        baseline_summary,
        current_summary,
        args.threshold,
    )

    markdown = render_markdown(
        baseline_summary,
        current_summary,
        args.threshold,
        comparison,
    )
    args.output.write_text(markdown, encoding="utf-8")

    print(markdown)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
