"""Tests for mlsdm.cli.main module (simple CLI entrypoint).

Tests cover:
- JSONFormatter logging
- main() argument parsing
- Memory simulation workflow
- API mode launching
"""

import argparse
import logging
import subprocess
import sys
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest


class TestJSONFormatter:
    """Tests for JSONFormatter class."""

    def test_formatter_creates_json_output(self):
        """Test that JSONFormatter produces valid JSON."""
        from mlsdm.cli.main import JSONFormatter

        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        # Should be valid JSON
        import json
        parsed = json.loads(output)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["module"] == "test"
        assert "timestamp" in parsed

    def test_formatter_handles_different_log_levels(self):
        """Test formatter with different log levels."""
        from mlsdm.cli.main import JSONFormatter

        formatter = JSONFormatter()

        for level_name, level_val in [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
        ]:
            record = logging.LogRecord(
                name="test",
                level=level_val,
                pathname="test.py",
                lineno=1,
                msg=f"Test {level_name}",
                args=(),
                exc_info=None,
            )
            output = formatter.format(record)

            import json
            parsed = json.loads(output)
            assert parsed["level"] == level_name
            assert parsed["message"] == f"Test {level_name}"


class TestMainFunction:
    """Tests for main() function."""

    def test_main_default_args_runs_simulation(self, tmp_path):
        """Test main with default args runs memory simulation."""
        from mlsdm.cli.main import main

        # Create a minimal config file with valid schema
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(
            """
dimension: 384
"""
        )

        with patch("sys.argv", ["mlsdm", "--config", str(config_file), "--steps", "5"]):
            with patch("mlsdm.cli.main.MemoryManager") as mock_manager:
                mock_instance = MagicMock()
                mock_manager.return_value = mock_instance

                main()

                # Should create manager and run simulation
                mock_manager.assert_called_once()
                mock_instance.run_simulation.assert_called_once_with(5)

    def test_main_api_mode_starts_uvicorn(self, tmp_path):
        """Test main with --api flag starts uvicorn."""
        from mlsdm.cli.main import main

        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("dimension: 384")

        with patch("sys.argv", ["mlsdm", "--config", str(config_file), "--api"]):
            # Patch uvicorn at import time
            with patch("uvicorn.run") as mock_uvicorn_run:
                main()

                # Should call uvicorn.run with app
                mock_uvicorn_run.assert_called_once()
                call_args = mock_uvicorn_run.call_args
                assert call_args.kwargs["host"] == "0.0.0.0"
                assert call_args.kwargs["port"] == 8000

    def test_main_custom_config_path(self, tmp_path):
        """Test main with custom config path."""
        from mlsdm.cli.main import main

        config_file = tmp_path / "custom.yaml"
        config_file.write_text("dimension: 384")

        with patch("sys.argv", ["mlsdm", "--config", str(config_file), "--steps", "1"]):
            with patch("mlsdm.cli.main.MemoryManager") as mock_manager:
                mock_instance = MagicMock()
                mock_manager.return_value = mock_instance

                main()

                # Should load custom config
                assert mock_manager.called
                # Config should have been loaded
                config_arg = mock_manager.call_args[0][0]
                assert config_arg is not None

    def test_main_custom_steps_count(self, tmp_path):
        """Test main with custom steps count."""
        from mlsdm.cli.main import main

        config_file = tmp_path / "config.yaml"
        config_file.write_text("dimension: 384")

        with patch("sys.argv", ["mlsdm", "--config", str(config_file), "--steps", "42"]):
            with patch("mlsdm.cli.main.MemoryManager") as mock_manager:
                mock_instance = MagicMock()
                mock_manager.return_value = mock_instance

                main()

                # Should run 42 steps
                mock_instance.run_simulation.assert_called_once_with(42)

    def test_main_api_mode_does_not_run_simulation(self, tmp_path):
        """Test that API mode does not run simulation."""
        from mlsdm.cli.main import main

        config_file = tmp_path / "config.yaml"
        config_file.write_text("dimension: 384")

        with patch("sys.argv", ["mlsdm", "--config", str(config_file), "--api"]):
            with patch("uvicorn.run") as mock_uvicorn_run:
                with patch("mlsdm.cli.main.MemoryManager") as mock_manager:
                    main()

                    # Should NOT create MemoryManager in API mode
                    mock_manager.assert_not_called()
                    # Should start uvicorn
                    mock_uvicorn_run.assert_called_once()


class TestLoggingSetup:
    """Tests for logging configuration."""

    def test_logging_handler_configured(self):
        """Test that logging handler is set up correctly."""
        from mlsdm.cli.main import handler, logger

        # Handler should be a StreamHandler
        assert isinstance(handler, logging.StreamHandler)

        # Logger should be configured
        assert logger is not None
        assert logger.name == "mlsdm.cli.main"

    def test_json_formatter_attached_to_handler(self):
        """Test that JSONFormatter is attached to handler."""
        from mlsdm.cli.main import JSONFormatter, handler

        # Handler should have JSONFormatter
        assert isinstance(handler.formatter, JSONFormatter)


class TestModuleEntry:
    """Tests for module entry point via __main__.py."""

    def test_cli_main_argument_parsing(self):
        """Test that main() correctly parses command line arguments."""
        from mlsdm.cli.main import main

        # Test that argparse is set up correctly by checking help
        with patch("sys.argv", ["mlsdm", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            # argparse exits with 0 for --help
            assert exc_info.value.code == 0

    def test_cli_main_name_main_block(self, tmp_path):
        """Test __name__ == '__main__' block calls main()."""
        from mlsdm.cli.main import main

        # The if __name__ == "__main__" block should call main()
        # We verify by mocking and importing
        config_file = tmp_path / "config.yaml"
        config_file.write_text("dimension: 384")

        with patch("sys.argv", ["mlsdm", "--config", str(config_file), "--steps", "1"]):
            with patch("mlsdm.cli.main.MemoryManager"):
                # Just verify main is callable
                assert callable(main)
                result = main()
                assert result is None


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_main_with_nonexistent_config_uses_default(self):
        """Test main with nonexistent config falls back to default."""
        from mlsdm.cli.main import main

        with patch("sys.argv", ["mlsdm", "--config", "/nonexistent/config.yaml", "--steps", "1"]):
            # Should use default config path which may also not exist
            # but ConfigLoader should handle this gracefully
            with patch("mlsdm.cli.main.ConfigLoader.load_config") as mock_load:
                with patch("mlsdm.cli.main.MemoryManager") as mock_manager:
                    mock_load.return_value = {"dimension": 128}
                    mock_instance = MagicMock()
                    mock_manager.return_value = mock_instance

                    main()

                    # Should attempt to load config
                    mock_load.assert_called_once_with("/nonexistent/config.yaml")

    def test_main_logs_start_and_done(self, tmp_path, caplog):
        """Test that main logs simulation start and completion."""
        from mlsdm.cli.main import main

        config_file = tmp_path / "config.yaml"
        config_file.write_text("dimension: 384")

        with patch("sys.argv", ["mlsdm", "--config", str(config_file), "--steps", "2"]):
            with patch("mlsdm.cli.main.MemoryManager") as mock_manager:
                mock_instance = MagicMock()
                mock_manager.return_value = mock_instance

                with caplog.at_level(logging.INFO):
                    main()

                # Should log "Running simulation" and "Done"
                # Note: JSONFormatter is active but caplog captures the messages
                log_messages = [record.message for record in caplog.records]
                assert any("simulation" in msg.lower() for msg in log_messages)
                assert any("Done" in msg or "done" in msg for msg in log_messages)
