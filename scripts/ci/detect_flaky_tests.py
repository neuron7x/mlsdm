#!/usr/bin/env python3
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class FlakeReport:
    runs: int
    results: List[int]

    @property
    def flaky(self) -> bool:
        return len(set(self.results)) > 1

    @property
    def success_rate(self) -> float:
        if self.runs == 0:
            return 0.0
        return self.results.count(0) / self.runs


def analyze_flakiness(runs: int = 5) -> FlakeReport:
    results: List[int] = []
    env = os.environ.copy()
    env.setdefault("PYTHONHASHSEED", "0")

    for _ in range(runs):
        completed = subprocess.run(
            ["pytest", "tests/", "-x", "-q"],
            env=env,
            check=False,
        )
        results.append(completed.returncode)

    return FlakeReport(runs=runs, results=results)


def main() -> int:
    report = analyze_flakiness()
    summary = {
        "runs": report.runs,
        "results": report.results,
        "flaky": report.flaky,
        "success_rate": report.success_rate,
    }
    if report.flaky:
        print(f"❌ Flaky tests detected: {summary}")
        return 1
    print(f"✓ No flakiness: {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
