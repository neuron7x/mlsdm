import json
import sys
from pathlib import Path

import scripts.ci.failure_intelligence as fi


def run_main(tmp_path: Path, args: list[str]) -> dict:
    out_md = tmp_path / "out.md"
    out_json = tmp_path / "out.json"
    argv = ["prog", "--out", str(out_md), "--json", str(out_json), *args]
    original = list(sys.argv)
    sys.argv = argv
    try:
        fi.main()
    finally:
        sys.argv = original
    assert out_md.exists()
    assert out_json.exists()
    return json.loads(out_json.read_text(encoding="utf-8"))


def test_missing_defusedxml_writes_outputs(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(fi, "HAS_DEFUSEDXML", False)
    monkeypatch.setattr(fi, "DEFUSEDXML_ERR", "ImportError('defusedxml')")
    monkeypatch.setattr(fi, "parse", None, raising=False)
    summary = run_main(tmp_path, [])
    assert any(err.get("code") == "defusedxml_missing" for err in summary.get("errors", []))
    assert summary["signal"].startswith("Failure intelligence")


def test_corrupt_xml_is_handled(tmp_path: Path):
    bad = tmp_path / "bad.xml"
    bad.write_text("<testsuite><testcase></testsuite", encoding="utf-8")
    summary = run_main(tmp_path, ["--junit", str(bad)])
    assert summary["top_failures"] == []


def test_happy_path_outputs(tmp_path: Path):
    junit = tmp_path / "junit.xml"
    junit.write_text(
        """
        <testsuite>
          <testcase classname="pkg.test_sample" name="test_one" file="tests/unit/test_sample.py">
            <failure message="assert 1 == 0">Traceback line 1</failure>
          </testcase>
        </testsuite>
        """,
        encoding="utf-8",
    )
    coverage = tmp_path / "coverage.xml"
    coverage.write_text('<coverage line-rate="0.5" branch-rate="0.1" version="1.0"></coverage>', encoding="utf-8")
    changed = tmp_path / "changed.txt"
    changed.write_text("src/mlsdm/core/module.py\n", encoding="utf-8")
    summary = run_main(tmp_path, ["--junit", str(junit), "--coverage", str(coverage), "--changed-files", str(changed)])
    assert summary["coverage_percent"] == 50.0
    assert summary["top_failures"][0]["id"] == "pkg.test_sample::test_one"


def test_missing_artifacts_emit_structured_errors(tmp_path: Path):
    missing_junit = tmp_path / "missing-junit.xml"
    missing_cov = tmp_path / "missing-cov.xml"
    summary = run_main(
        tmp_path,
        [
            "--junit",
            str(missing_junit),
            "--coverage",
            str(missing_cov),
            "--changed-files",
            str(tmp_path / "missing-changed.txt"),
        ],
    )
    assert summary["status"] == "degraded"
    assert summary["errors"] == summary["input_integrity"]
    assert summary["errors"] == [
        {"code": "artifact_missing", "artifact": "coverage", "path": str(missing_cov)},
        {"code": "artifact_missing", "artifact": "junit", "path": str(missing_junit)},
        {"code": "input_missing", "artifact": "changed_files", "path": str(tmp_path / "missing-changed.txt")},
    ]
