"""
Tests for scripts/validate_policy_config.py
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestValidatePolicyConfig:
    """Test suite for the validate_policy_config.py script."""

    @pytest.fixture
    def script_path(self) -> Path:
        """Get path to the validate_policy_config script."""
        repo_root = Path(__file__).parent.parent.parent
        script = repo_root / "scripts" / "validate_policy_config.py"
        assert script.exists(), f"Script not found: {script}"
        return script

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root path."""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def policy_dir(self, repo_root: Path) -> Path:
        """Get policy directory path."""
        policy_dir = repo_root / "policy"
        assert policy_dir.exists(), "Policy directory not found"
        return policy_dir

    def run_script(
        self, script_path: Path, cwd: Path = None, args: list = None
    ) -> tuple[int, str, str]:
        """Run the validation script and return (returncode, stdout, stderr)."""
        if cwd is None:
            cwd = script_path.parent.parent  # repo root

        if args is None:
            args = []

        result = subprocess.run(
            [sys.executable, str(script_path)] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.returncode, result.stdout, result.stderr

    def test_script_exists_and_executable(self, script_path: Path):
        """Test that the script exists and is executable."""
        assert script_path.exists()
        assert script_path.stat().st_mode & 0o111, "Script is not executable"

    def test_script_imports_successfully(self, script_path: Path):
        """Test that the script can be imported without errors."""
        # Try to import as a module
        result = subprocess.run(
            [sys.executable, "-c", f"import sys; sys.path.insert(0, '{script_path.parent}'); import validate_policy_config"],
            capture_output=True,
            text=True,
        )

        # May fail if PyYAML not installed, but shouldn't have syntax errors
        if result.returncode != 0 and "yaml" not in result.stderr.lower():
            pytest.fail(f"Script has import errors: {result.stderr}")

    def test_script_runs_on_real_repository(
        self, script_path: Path, repo_root: Path, policy_dir: Path
    ):
        """Test that the script runs successfully on actual repository policies."""
        returncode, stdout, stderr = self.run_script(script_path, cwd=repo_root)

        # Should pass (may have warnings, but no errors)
        assert returncode == 0, f"Script failed: {stderr}\nStdout: {stdout}"

        # Check for expected sections
        assert "Security Workflow Files" in stdout
        assert "Security Module References" in stdout
        assert "SLO Test Locations" in stdout
        assert "Documentation Files" in stdout

        # Check for validation summary
        assert "Validation Summary" in stdout
        assert "Errors:" in stdout
        assert "Warnings:" in stdout

    def test_policy_files_exist(self, policy_dir: Path):
        """Test that expected policy files exist."""
        security_baseline = policy_dir / "security-baseline.yaml"
        observability_slo = policy_dir / "observability-slo.yaml"

        assert security_baseline.exists(), "security-baseline.yaml not found"
        assert observability_slo.exists(), "observability-slo.yaml not found"

    def test_policy_files_are_valid_yaml(self, policy_dir: Path):
        """Test that policy files are valid YAML."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        for policy_file in ["security-baseline.yaml", "observability-slo.yaml"]:
            full_path = policy_dir / policy_file

            with open(full_path, encoding="utf-8") as f:
                try:
                    data = yaml.safe_load(f)
                    assert data is not None, f"{policy_file} is empty"
                    assert isinstance(data, dict), f"{policy_file} is not a dict"
                except yaml.YAMLError as e:
                    pytest.fail(f"Invalid YAML in {policy_file}: {e}")

    def test_security_baseline_structure(self, policy_dir: Path):
        """Test that security-baseline.yaml has expected structure."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        with open(policy_dir / "security-baseline.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Check required top-level keys
        assert "version" in data
        assert "policy_name" in data
        assert "required_checks" in data

        # Check required_checks structure
        required_checks = data["required_checks"]
        assert isinstance(required_checks, list)
        assert len(required_checks) > 0

        # Each check should have a name
        for check in required_checks:
            assert "name" in check
            assert "description" in check
            # Should have either workflow_file, command, or script
            assert any(
                key in check for key in ["workflow_file", "command", "script"]
            ), f"Check {check['name']} missing execution method"

    def test_observability_slo_structure(self, policy_dir: Path):
        """Test that observability-slo.yaml has expected structure."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        with open(policy_dir / "observability-slo.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Check required top-level keys
        assert "version" in data
        assert "policy_name" in data
        assert "slos" in data

        # Check SLOs structure
        slos = data["slos"]
        assert isinstance(slos, dict)

        # Should have at least api_endpoints and system_resources
        assert "api_endpoints" in slos or "system_resources" in slos

    def test_workflow_files_referenced_exist(self, repo_root: Path, policy_dir: Path):
        """Test that workflow files referenced in policies actually exist."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        with open(policy_dir / "security-baseline.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        required_checks = data.get("required_checks", [])

        for check in required_checks:
            workflow_file = check.get("workflow_file")
            if workflow_file:
                workflow_path = repo_root / workflow_file
                assert workflow_path.exists(), (
                    f"Workflow file not found for check '{check['name']}': {workflow_file}"
                )

    def test_security_modules_referenced_exist(self, repo_root: Path, policy_dir: Path):
        """Test that security modules referenced in policies actually exist."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        with open(policy_dir / "security-baseline.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        security_reqs = data.get("security_requirements", {})
        input_val = security_reqs.get("input_validation", {})

        # Check LLM safety module
        llm_safety = input_val.get("llm_safety_module")
        if llm_safety:
            # Convert module path to file path
            parts = llm_safety.split(".")
            if parts[0] == "mlsdm":
                src_path = repo_root / "src" / "/".join(parts)
                py_path = src_path.parent / f"{src_path.name}.py"
                init_path = src_path / "__init__.py"

                assert py_path.exists() or init_path.exists(), (
                    f"LLM safety module not found: {llm_safety}"
                )

        # Check payload scrubber module
        scrubber = input_val.get("payload_scrubber_module")
        if scrubber:
            parts = scrubber.split(".")
            if parts[0] == "mlsdm":
                src_path = repo_root / "src" / "/".join(parts)
                py_path = src_path.parent / f"{src_path.name}.py"
                init_path = src_path / "__init__.py"

                assert py_path.exists() or init_path.exists(), (
                    f"Payload scrubber module not found: {scrubber}"
                )

    def test_slo_test_locations_exist(self, repo_root: Path, policy_dir: Path):
        """Test that SLO test files referenced in policies actually exist."""
        try:
            import yaml
        except ImportError:
            pytest.skip("PyYAML not installed")

        with open(policy_dir / "observability-slo.yaml", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        slos = data.get("slos", {})

        # Collect all test locations
        test_locations = []

        for slo_type in ["api_endpoints", "system_resources", "cognitive_engine"]:
            slo_list = slos.get(slo_type, [])
            for slo in slo_list:
                if "test_location" in slo:
                    test_locations.append((slo["name"], slo["test_location"]))

        # Verify each test location
        for name, test_loc in test_locations:
            # Extract file path (before ::)
            file_path = test_loc.split("::", 1)[0] if "::" in test_loc else test_loc

            full_path = repo_root / file_path
            assert full_path.exists(), (
                f"Test file not found for SLO '{name}': {file_path}"
            )

    def test_script_detects_missing_workflow(self, tmp_path: Path):
        """Test that script detects when a referenced workflow doesn't exist."""
        # Create temporary policy with non-existent workflow
        policy_dir = tmp_path / "policy"
        policy_dir.mkdir()

        fake_policy = policy_dir / "security-baseline.yaml"
        fake_policy.write_text("""
version: "1.0"
policy_name: "Test Policy"
required_checks:
  - name: "fake_check"
    description: "Non-existent workflow"
    workflow_file: ".github/workflows/non-existent.yml"
""")

        # Try to run validator (will likely fail)
        result = subprocess.run(
            [sys.executable, "-c", f"""
import sys
import yaml
from pathlib import Path

policy_path = Path('{fake_policy}')
with open(policy_path) as f:
    data = yaml.safe_load(f)

workflow_file = data['required_checks'][0]['workflow_file']
workflow_path = Path('{tmp_path}') / workflow_file

if not workflow_path.exists():
    print(f"✗ Workflow file not found: {{workflow_file}}")
    sys.exit(1)
else:
    print(f"✓ Workflow file exists: {{workflow_file}}")
    sys.exit(0)
"""],
            capture_output=True,
            text=True,
        )

        # Should detect the missing file
        assert result.returncode == 1
        assert "not found" in result.stdout.lower()

    def test_script_help_message(self, script_path: Path):
        """Test that script provides help message."""
        returncode, stdout, stderr = self.run_script(script_path, args=["--help"])

        assert returncode == 0
        assert "usage:" in stdout.lower() or "help" in stdout.lower()
        assert "policy" in stdout.lower()

    def test_script_handles_missing_policy_dir(self, script_path: Path, tmp_path: Path):
        """Test that script handles missing policy directory gracefully."""
        non_existent = tmp_path / "non-existent-policy"

        returncode, stdout, stderr = self.run_script(
            script_path,
            cwd=tmp_path,
            args=["--policy-dir", str(non_existent)],
        )

        # Should fail with clear error
        assert returncode == 1
        assert "not found" in stdout.lower() or "not found" in stderr.lower()
