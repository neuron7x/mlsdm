from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import mlsdm.policy.validation as policy_validation
from mlsdm.policy.loader import PolicyLoadError
from mlsdm.policy.validation import PolicyValidator


def _bundle_for_validation(
    *,
    workflow_file: str,
    script_path: str,
    llm_module: str,
    scrubber_module: str,
    test_location: str,
    doc_paths: dict[str, str],
) -> SimpleNamespace:
    required_checks = [
        SimpleNamespace(name="workflow", workflow_file=workflow_file, command=None, script=None),
        SimpleNamespace(name="script", workflow_file=None, command=None, script=script_path),
        SimpleNamespace(name="command", workflow_file=None, command="pytest", script=None),
    ]
    security_requirements = SimpleNamespace(
        input_validation=SimpleNamespace(
            llm_safety_module=llm_module,
            payload_scrubber_module=scrubber_module,
        )
    )
    security_controls = SimpleNamespace(
        required_checks=required_checks,
        security_requirements=security_requirements,
    )
    security_baseline = SimpleNamespace(controls=security_controls)

    slos = SimpleNamespace(
        api_endpoints=[SimpleNamespace(name="api", test_location=test_location)],
        system_resources=[],
        cognitive_engine=[],
    )
    observability_thresholds = SimpleNamespace(slos=slos)
    documentation = SimpleNamespace(**doc_paths)
    observability_controls = SimpleNamespace(documentation=documentation)
    observability_slo = SimpleNamespace(
        thresholds=observability_thresholds,
        controls=observability_controls,
    )

    return SimpleNamespace(
        security_baseline=security_baseline,
        observability_slo=observability_slo,
    )


def test_validate_all_handles_policy_load_error(tmp_path: Path, monkeypatch) -> None:
    validator = PolicyValidator(repo_root=tmp_path, policy_dir=tmp_path)

    def _raise(_policy_dir: Path) -> None:
        raise PolicyLoadError("missing")

    monkeypatch.setattr(policy_validation, "load_policy_bundle", _raise)

    assert validator.validate_all() is False
    assert validator.errors


def test_validation_collects_errors_and_warnings(tmp_path: Path) -> None:
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    (workflows_dir / "ci.yml").write_text("name: ci", encoding="utf-8")

    scripts_dir = tmp_path / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "policy.sh").write_text("echo ok", encoding="utf-8")

    test_file = tmp_path / "tests" / "slo" / "test_api.py"
    test_file.parent.mkdir(parents=True)
    test_file.write_text("def test_api(): pass", encoding="utf-8")

    doc_file = tmp_path / "docs" / "slo.md"
    doc_file.parent.mkdir(parents=True)
    doc_file.write_text("slo", encoding="utf-8")

    bundle = _bundle_for_validation(
        workflow_file=".github/workflows/missing.yml",
        script_path="./scripts/policy.sh",
        llm_module="mlsdm.security.llm_safety",
        scrubber_module="mlsdm.security.missing_module",
        test_location="tests/slo/test_api.py::test_api",
        doc_paths={
            "slo_spec": "docs/slo.md",
            "validation_protocol": "docs/missing.md",
            "runbook": "docs/runbook.md",
            "observability_guide": "docs/observability.md",
        },
    )

    validator = PolicyValidator(repo_root=tmp_path, policy_dir=tmp_path)
    validator._validate_security_workflows(bundle)
    validator._validate_security_modules(bundle)
    validator._validate_slo_tests(bundle)
    validator._validate_documentation(bundle)
    validator._print_results()

    assert validator.errors
    assert validator.warnings
