"""CI evidence collector for readiness automation."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[2]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_posix(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _safe_parse_junit(path: Path) -> list[dict[str, Any]] | None:
    try:
        tree = ElementTree.parse(path)
    except (OSError, ElementTree.ParseError):
        return None

    root = tree.getroot()
    suites = list(root.iter("testsuite")) if root.tag != "testsuite" else [root]
    parsed: list[dict[str, Any]] = []
    for suite in suites:
        name = suite.attrib.get("name", "").lower()
        suite_type = "unknown"
        if "unit" in name:
            suite_type = "unit"
        elif "integration" in name:
            suite_type = "integration"
        elif "property" in name:
            suite_type = "property"
        elif "e2e" in name or "endtoend" in name:
            suite_type = "e2e"
        elif "security" in name:
            suite_type = "security"

        testcases = list(suite.iter("testcase"))
        tests_attr = suite.attrib.get("tests")
        try:
            tests = int(float(tests_attr)) if tests_attr is not None else len(testcases)
        except (TypeError, ValueError):
            tests = len(testcases)
        failures_attr = suite.attrib.get("failures")
        errors_attr = suite.attrib.get("errors")
        skipped_attr = suite.attrib.get("skipped")
        try:
            failures = int(float(failures_attr)) if failures_attr is not None else 0
        except (TypeError, ValueError):
            failures = 0
        try:
            errors = int(float(errors_attr)) if errors_attr is not None else 0
        except (TypeError, ValueError):
            errors = 0
        try:
            skipped = int(float(skipped_attr)) if skipped_attr is not None else 0
        except (TypeError, ValueError):
            skipped = 0
        time_raw = suite.attrib.get("time", "0")
        try:
            duration = float(time_raw)
        except (TypeError, ValueError):
            duration = 0.0

        failure_entries: list[dict[str, str]] = []
        for case in testcases:
            case_failures = list(case.findall("failure")) + list(case.findall("error"))
            for node in case_failures:
                failure_entries.append(
                    {
                        "classname": case.attrib.get("classname", ""),
                        "name": case.attrib.get("name", ""),
                        "message": (node.attrib.get("message") or "").strip(),
                    }
                )

        parsed.append(
            {
                "suite": suite_type,
                "passed": max(tests - failures - errors - skipped, 0),
                "failed": failures + errors,
                "skipped": skipped,
                "duration_seconds": duration,
                "failures": failure_entries,
            }
        )
    return parsed


def _aggregate_suites(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = ["unit", "integration", "property", "e2e", "security", "unknown"]
    aggregated: dict[str, dict[str, Any]] = {
        key: {
            "suite": key,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": 0.0,
            "failures": [],
        }
        for key in order
    }
    seen: set[str] = set()
    for entry in entries:
        suite = entry.get("suite", "unknown")
        if suite not in aggregated:
            suite = "unknown"
        agg = aggregated[suite]
        agg["passed"] += int(entry.get("passed", 0))
        agg["failed"] += int(entry.get("failed", 0))
        agg["skipped"] += int(entry.get("skipped", 0))
        agg["duration_seconds"] += float(entry.get("duration_seconds", 0.0))
        agg["failures"].extend(entry.get("failures", []))
        seen.add(suite)

    suites = [
        aggregated[name]
        for name in order
        if name in seen or aggregated[name]["passed"] or aggregated[name]["failed"] or aggregated[name]["skipped"]
    ]
    return suites


def _parse_coverage(path: Path) -> tuple[float, float] | None:
    try:
        tree = ElementTree.parse(path)
    except (OSError, ElementTree.ParseError):
        return None

    root = tree.getroot()
    line_rate = root.attrib.get("line-rate") or root.attrib.get("lineRate")
    branch_rate = root.attrib.get("branch-rate") or root.attrib.get("branchRate")
    try:
        return float(line_rate), float(branch_rate)
    except (TypeError, ValueError):
        return None


def _load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _count_bandit(payload: Any) -> tuple[int, int, int] | None:
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return None
    high = medium = low = 0
    for item in results:
        if not isinstance(item, dict):
            continue
        sev = str(item.get("issue_severity", "")).lower()
        if sev == "high":
            high += 1
        elif sev == "medium":
            medium += 1
        elif sev == "low":
            low += 1
    return high, medium, low


def _count_semgrep(payload: Any) -> tuple[int, int, int] | None:
    results = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return None
    high = medium = low = 0
    for item in results:
        if not isinstance(item, dict):
            continue
        sev = ""
        if "extra" in item and isinstance(item["extra"], dict):
            sev = str(item["extra"].get("severity", "")).lower()
        elif "severity" in item:
            sev = str(item.get("severity", "")).lower()
        if sev in ("error", "high", "critical"):
            high += 1
        elif sev in ("medium", "warning"):
            medium += 1
        elif sev:
            low += 1
    return high, medium, low


def _count_gitleaks(payload: Any) -> tuple[int, int, int] | None:
    results = payload if isinstance(payload, list) else payload.get("findings") if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return None
    high = medium = low = 0
    for item in results:
        if not isinstance(item, dict):
            continue
        sev = str(item.get("severity") or item.get("Severity") or "").lower()
        if sev in ("critical", "high"):
            high += 1
        elif sev == "medium":
            medium += 1
        elif sev:
            low += 1
        else:
            high += 1  # default conservative
    return high, medium, low


def collect_evidence(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    junit_files = sorted((root / "reports").glob("junit-*.xml"))
    coverage_paths = [root / "coverage.xml", root / "reports" / "coverage.xml"]
    security_paths = {
        "bandit": root / "reports" / "bandit.json",
        "semgrep": root / "reports" / "semgrep.json",
        "gitleaks": root / "reports" / "gitleaks.json",
    }
    performance_path = root / "reports" / "benchmark_results.json"

    timestamp = _now().isoformat()

    junit_entries: list[dict[str, Any]] = []
    junit_measured = True
    for path in junit_files:
        parsed = _safe_parse_junit(path)
        if parsed is None:
            junit_measured = False
            junit_entries = []
            break
        junit_entries.extend(parsed)
    suites = _aggregate_suites(junit_entries) if junit_entries else []
    totals = {
        "passed": sum(s["passed"] for s in suites),
        "failed": sum(s["failed"] for s in suites),
        "skipped": sum(s["skipped"] for s in suites),
        "duration_seconds": round(sum(s["duration_seconds"] for s in suites), 6),
    }
    tests_section = {"suites": suites, "totals": totals}

    cov_measured = False
    cov_line = 0.0
    cov_branch = 0.0
    cov_path_found: Path | None = None
    for path in coverage_paths:
        if path.exists():
            cov_path_found = path
            parsed = _parse_coverage(path)
            if parsed:
                cov_measured = True
                cov_line, cov_branch = parsed
            break

    security_entries: list[dict[str, Any]] = []
    security_measured = False
    for tool_name, path in security_paths.items():
        if not path.exists():
            continue
        counts: tuple[int, int, int] | None = None
        payload = _load_json(path)
        if tool_name == "bandit":
            counts = _count_bandit(payload) if payload is not None else None
        elif tool_name == "semgrep":
            counts = _count_semgrep(payload) if payload is not None else None
        elif tool_name == "gitleaks":
            counts = _count_gitleaks(payload) if payload is not None else None
        measured = counts is not None
        security_measured = security_measured or measured
        high, medium, low = counts if counts else (0, 0, 0)
        security_entries.append(
            {
                "tool": tool_name,
                "high": high,
                "medium": medium,
                "low": low,
                "measured": measured,
            }
        )
    security_entries = sorted(security_entries, key=lambda x: x["tool"])

    perf_measured = False
    if performance_path.exists():
        payload = _load_json(performance_path)
        perf_measured = payload is not None

    evidence: dict[str, Any] = {
        "timestamp_utc": timestamp,
        "sources": {
            "junit": {"found": bool(junit_files), "files": [_as_posix(p, root) for p in junit_files]},
            "coverage": {"found": cov_path_found is not None, "path": _as_posix(cov_path_found, root) if cov_path_found else None},
            "security": {"found": any(p.exists() for p in security_paths.values()), "files": sorted(_as_posix(p, root) for p in security_paths.values() if p.exists())},
            "performance": {"found": performance_path.exists(), "path": _as_posix(performance_path, root) if performance_path.exists() else None},
        },
        "tests": tests_section,
        "coverage": {
            "line_rate": cov_line,
            "branch_rate": cov_branch,
            "measured": cov_measured,
        },
        "security": {
            "tools": security_entries,
            "measured": security_measured,
        },
        "performance": {"measured": perf_measured},
    }

    canonical = json.dumps(evidence, sort_keys=True, separators=(",", ":"))
    evidence_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    evidence["evidence_hash"] = f"sha256-{evidence_hash}"
    if not junit_measured:
        evidence["tests"] = tests_section
    return evidence


def _write_output(payload: dict[str, Any], output: str | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if not output:
        print(text)
        return
    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(out_path.suffix + ".tmp")
    tmp_path.write_text(text + "\n", encoding="utf-8")
    tmp_path.replace(out_path)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect readiness evidence from local artifacts")
    parser.add_argument("--root", default=str(ROOT), help="Repository root (default: project root)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        evidence = collect_evidence(Path(args.root))
        _write_output(evidence, args.output)
        return 0
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import sys

    raise SystemExit(main(sys.argv[1:]))
