from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CoverageStats:
    lines: int = 0
    covered: int = 0

    def add(self, hits: int) -> None:
        self.lines += 1
        if hits > 0:
            self.covered += 1

    def percent(self) -> float:
        if self.lines == 0:
            return 0.0
        return round((self.covered / self.lines) * 100, 2)


def _normalize_path(filename: str, root: str) -> str | None:
    if filename.startswith(root):
        return filename

    path = Path(filename)
    if not path.is_absolute():
        return f"{root.rstrip('/')}/{filename.lstrip('/')}"

    parts = path.as_posix().split("/")
    if "src" in parts:
        try:
            src_index = parts.index("src")
        except ValueError:
            return None
        candidate = "/".join(parts[src_index:])
        if candidate.startswith(root):
            return candidate
    return None


def _collect_coverage(coverage_xml: Path, *, root: str) -> dict[str, CoverageStats]:
    tree = ET.parse(coverage_xml)
    root_element = tree.getroot()

    stats: dict[str, CoverageStats] = {}

    for class_element in root_element.iter("class"):
        filename = class_element.attrib.get("filename")
        if not filename:
            continue
        normalized = _normalize_path(filename, root)
        if normalized is None:
            continue
        filename = normalized
        file_stats = stats.setdefault(filename, CoverageStats())
        lines_element = class_element.find("lines")
        if lines_element is None:
            continue
        for line_element in lines_element.iter("line"):
            hits = int(line_element.attrib.get("hits", "0"))
            file_stats.add(hits)

    return stats


def _write_summary(stats: dict[str, CoverageStats], output_path: Path, *, root: str) -> None:
    modules = [
        {
            "path": path,
            "lines": data.lines,
            "covered": data.covered,
            "percent": data.percent(),
        }
        for path, data in sorted(stats.items())
    ]

    total_lines = sum(item["lines"] for item in modules)
    total_covered = sum(item["covered"] for item in modules)
    total_percent = 0.0 if total_lines == 0 else round((total_covered / total_lines) * 100, 2)

    payload = {
        "schema_version": 1,
        "measured_paths_root": root,
        "modules": modules,
        "totals": {
            "lines": total_lines,
            "covered": total_covered,
            "percent": total_percent,
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize coverage.xml for src/mlsdm modules")
    parser.add_argument("--coverage-xml", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--root", default="src/mlsdm", type=str)
    args = parser.parse_args()

    if not args.coverage_xml.exists():
        print(f"ERROR: coverage.xml not found at {args.coverage_xml}", file=sys.stderr)
        return 2

    try:
        stats = _collect_coverage(args.coverage_xml, root=args.root)
        _write_summary(stats, args.out, root=args.root)
    except Exception as exc:  # pragma: no cover - unexpected error handling
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
