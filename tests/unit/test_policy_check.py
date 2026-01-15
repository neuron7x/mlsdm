from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import mlsdm.policy.check as policy_check
from mlsdm.policy.loader import PolicyLoadError


@dataclass
class DummyResult:
    returncode: int
    stdout: str = ""
    stderr: str = ""


class DummyValidator:
    def __init__(self, repo_root: Path, policy_dir: Path) -> None:
        self.repo_root = repo_root
        self.policy_dir = policy_dir

    def validate_all(self) -> bool:
        return False


def test_resolve_paths_and_workflow_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(policy_check, "REPO_ROOT", tmp_path)

    policy_dir = policy_check._resolve_policy_dir(Path("policy"))
    output_path = policy_check._resolve_output_path(Path("build/output.json"))

    assert policy_dir == tmp_path / "policy"
    assert output_path == tmp_path / "build" / "output.json"

    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "b.yml").write_text("name: b", encoding="utf-8")
    (workflows_dir / "a.yml").write_text("name: a", encoding="utf-8")

    workflows = policy_check._workflow_files(tmp_path)
    assert workflows == [
        str(workflows_dir / "a.yml"),
        str(workflows_dir / "b.yml"),
    ]


def test_run_policy_checks_handles_unknown_stage(tmp_path: Path) -> None:
    result = policy_check.run_policy_checks(
        repo_root=tmp_path,
        policy_dir=tmp_path,
        rego_dir=tmp_path,
        data_output=tmp_path / "policy.json",
        stage="unknown",
    )
    assert result == 2


def test_run_policy_checks_validate_stage_failure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(policy_check, "PolicyValidator", DummyValidator)

    result = policy_check.run_policy_checks(
        repo_root=tmp_path,
        policy_dir=tmp_path,
        rego_dir=tmp_path,
        data_output=tmp_path / "policy.json",
        stage="validate",
    )
    assert result == 1


def test_run_policy_checks_export_failure(tmp_path: Path, monkeypatch) -> None:
    def _raise(*_args, **_kwargs) -> None:
        raise PolicyLoadError("boom")

    monkeypatch.setattr(policy_check, "export_opa_policy_data", _raise)

    result = policy_check.run_policy_checks(
        repo_root=tmp_path,
        policy_dir=tmp_path,
        rego_dir=tmp_path,
        data_output=tmp_path / "policy.json",
        stage="export",
    )
    assert result == 1


def test_run_policy_checks_missing_data_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(policy_check, "ensure_conftest_available", lambda: None)

    result = policy_check.run_policy_checks(
        repo_root=tmp_path,
        policy_dir=tmp_path,
        rego_dir=tmp_path,
        data_output=tmp_path / "policy.json",
        stage="workflows",
    )
    assert result == 1


def test_run_policy_checks_workflow_failure(tmp_path: Path, monkeypatch) -> None:
    data_output = tmp_path / "policy.json"
    data_output.write_text("{}", encoding="utf-8")

    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "ci.yml").write_text("name: ci", encoding="utf-8")

    monkeypatch.setattr(policy_check, "ensure_conftest_available", lambda: None)
    monkeypatch.setattr(policy_check, "run_conftest", lambda *_args, **_kwargs: DummyResult(1))

    result = policy_check.run_policy_checks(
        repo_root=tmp_path,
        policy_dir=tmp_path,
        rego_dir=tmp_path,
        data_output=data_output,
        stage="workflows",
    )
    assert result == 1
