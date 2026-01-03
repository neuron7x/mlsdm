import sys
from pathlib import Path

import pytest

from scripts.ci import export_requirements


def _generate() -> str:
    pyproject = export_requirements.load_pyproject(export_requirements.PYPROJECT_PATH)
    deps = export_requirements.parse_pyproject_deps(pyproject)
    return export_requirements.generate_requirements(deps)


def test_all_optional_groups_are_represented():
    pyproject = export_requirements.load_pyproject(export_requirements.PYPROJECT_PATH)
    deps = export_requirements.parse_pyproject_deps(pyproject)
    content = export_requirements.generate_requirements(deps)

    for group in deps["optional"].keys():
        header = (
            f"# Optional {export_requirements._title_case_group(group)} "
            f"(from pyproject.toml [project.optional-dependencies].{group})"
        )
        assert header in content


def test_generation_is_deterministic():
    assert _generate() == _generate()


def test_contract_header_matches_content():
    pyproject = export_requirements.load_pyproject(export_requirements.PYPROJECT_PATH)
    deps = export_requirements.parse_pyproject_deps(pyproject)
    content = export_requirements.generate_requirements(deps)

    ordered_groups = export_requirements._order_optional_groups(deps["optional"].keys())
    group_list = ", ".join(ordered_groups)

    assert (
        f"# Optional dependency groups discovered in pyproject.toml (ordered): {group_list}"
        in content
    )
    assert (
        f"# Optional dependency groups included in this file: all ({group_list})" in content
    )
    assert "# Excluded packages (not exported):" in content
    for name, reason in export_requirements.EXCLUDED_PACKAGES.items():
        assert f"# - {name}: {reason}" in content

    non_comment_lines = [line for line in content.splitlines() if line and not line.startswith("#")]
    for line in non_comment_lines:
        assert line in export_requirements.filter_excluded_dependencies([line])
    assert "sentence-transformers>=3.0.0" in content
    assert content.count("sentence-transformers>=3.0.0") == 1


def test_check_mode_detects_drift(tmp_path: Path, monkeypatch, capsys):
    tmp_req = tmp_path / "requirements.txt"
    tmp_req.write_text("stale\n", encoding="utf-8")

    monkeypatch.setattr(export_requirements, "REQUIREMENTS_PATH", tmp_req)
    monkeypatch.setattr(sys, "argv", ["export_requirements.py", "--check"])

    result = export_requirements.main()
    captured = capsys.readouterr()

    assert result == 1
    assert "First difference at line" in captured.err
    assert "python scripts/ci/export_requirements.py" in captured.err


def test_check_mode_passes_when_synced(tmp_path: Path, monkeypatch, capsys):
    generated = _generate()
    tmp_req = tmp_path / "requirements.txt"
    tmp_req.write_text(generated, encoding="utf-8")

    monkeypatch.setattr(export_requirements, "REQUIREMENTS_PATH", tmp_req)
    monkeypatch.setattr(sys, "argv", ["export_requirements.py", "--check"])

    result = export_requirements.main()
    captured = capsys.readouterr()

    assert result == 0
    assert "in sync" in captured.out
