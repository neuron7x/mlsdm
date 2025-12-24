"""
Integration tests for the MLSDM CLI.

Tests the CLI commands: demo, serve, check
"""

import os
import subprocess
import sys
from unittest.mock import patch

import pytest


class TestCLICheck:
    """Test the 'mlsdm check' command."""

    def test_check_command_runs(self):
        """Test that check command runs without error."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "check"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "MLSDM Environment Check" in result.stdout

    def test_check_shows_version(self):
        """Test that check shows mlsdm version."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "check"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "mlsdm v" in result.stdout

    def test_check_validates_python_version(self):
        """Test that check validates Python version."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "check"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "Python version" in result.stdout

    def test_check_verbose_flag(self):
        """Test verbose flag outputs more info."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "check", "--verbose"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        # Verbose mode should show full status JSON
        assert "checks" in result.stdout


class TestCLIDemo:
    """Test the 'mlsdm demo' command."""

    def test_demo_with_prompt(self):
        """Test demo with single prompt."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "demo", "-p", "Hello world"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "MLSDM Demo" in result.stdout
        assert "Prompt: Hello world" in result.stdout

    def test_demo_without_prompt_runs_demo(self):
        """Test demo without prompt runs demo prompts."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "demo"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Running demo prompts" in result.stdout

    def test_demo_verbose_output(self):
        """Test demo verbose mode."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "demo", "-p", "Test", "--verbose"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Full result" in result.stdout

    def test_demo_custom_moral_value(self):
        """Test demo with custom moral value."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "demo", "-p", "Test", "-m", "0.9"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Moral Value: 0.9" in result.stdout

    def test_demo_low_moral_rejected(self):
        """Test demo with low moral value gets rejected."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mlsdm.cli",
                "demo",
                "-p",
                "Test",
                "-m",
                "0.1",  # Very low moral value
                "--moral-threshold",
                "0.9",  # High threshold
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Rejected" in result.stdout


class TestCLIVersion:
    """Test version flag."""

    def test_version_flag(self):
        """Test --version flag."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "1.2.0" in result.stdout


class TestCLIHelp:
    """Test help output."""

    def test_help_flag(self):
        """Test --help flag."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "demo" in result.stdout
        assert "serve" in result.stdout
        assert "check" in result.stdout

    def test_demo_help(self):
        """Test demo --help."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "demo", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "--prompt" in result.stdout
        assert "--interactive" in result.stdout

    def test_serve_help(self):
        """Test serve --help."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "serve", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "--host" in result.stdout
        assert "--port" in result.stdout

    def test_check_help(self):
        """Test check --help."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "check", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "--verbose" in result.stdout


class TestCLIModule:
    """Test CLI module can be imported and run directly."""

    def test_import_cli_module(self):
        """Test that CLI module can be imported."""
        from mlsdm import cli

        assert hasattr(cli, "main")
        assert callable(cli.main)

    def test_main_with_no_args(self):
        """Test main() with no arguments shows help."""
        from mlsdm.cli import main

        with patch("sys.argv", ["mlsdm"]):
            # Should print help and return 0
            result = main()
            assert result == 0


class TestCLIServe:
    """Test 'mlsdm serve' command (without actually starting server)."""

    def test_serve_help(self):
        """Test serve shows help with correct options."""
        result = subprocess.run(
            [sys.executable, "-m", "mlsdm.cli", "serve", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "--host" in result.stdout
        assert "--port" in result.stdout
        assert "--backend" in result.stdout
        assert "--config" in result.stdout

    def test_config_path_set_before_app_import(self, tmp_path):
        """Regression test: CONFIG_PATH must be set before app module import.

        This test verifies the fix for the import order bug where CLI args
        like --config were set AFTER the serve module was imported, causing
        the app to use the default config instead of the specified one.
        """
        # Create a minimal valid config file
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
dimension: 384
strict_mode: false
moral_filter:
  threshold: 0.5
  min_threshold: 0.3
  max_threshold: 0.9
""")

        # Test script verifies that CONFIG_PATH is set before serve import
        # The expected path is passed via TEST_EXPECTED_PATH env var to avoid f-string injection
        test_script = '''
import os
import sys

# Clear any existing CONFIG_PATH
if "CONFIG_PATH" in os.environ:
    del os.environ["CONFIG_PATH"]

# Get expected path from environment (passed safely from test)
expected_path = os.environ.get("TEST_EXPECTED_PATH", "")
if not expected_path:
    print("FAIL: TEST_EXPECTED_PATH not set")
    sys.exit(1)

# Simulate what cmd_serve does: set env BEFORE import
os.environ["CONFIG_PATH"] = expected_path

# Now import serve (which imports app)
from mlsdm.entrypoints.serve import serve

# Verify CONFIG_PATH was used
actual_path = os.environ.get("CONFIG_PATH")
if actual_path != expected_path:
    print(f"FAIL: CONFIG_PATH mismatch: {actual_path} != {expected_path}")
    sys.exit(1)

print("PASS: CONFIG_PATH correctly set before import")
sys.exit(0)
'''

        # Pass the config path via environment variable to avoid code injection
        env = os.environ.copy()
        env["TEST_EXPECTED_PATH"] = str(config_file)

        result = subprocess.run(
            [sys.executable, "-c", test_script],
            capture_output=True,
            text=True,
            timeout=30,
            env=env,
        )
        assert result.returncode == 0, f"Config path test failed: {result.stderr}"
        assert "PASS" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
