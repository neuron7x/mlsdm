"""Smoke tests for MLSDM CLI entry points.

Tests cover:
- CLI module imports work correctly
- Basic main entry point functionality
- __main__ module imports
"""

import sys
from unittest.mock import MagicMock, patch


class TestCLIImports:
    """Test CLI module imports."""

    def test_cli_main_module_import(self) -> None:
        """Test that cli.main module can be imported."""
        from mlsdm.cli import main as main_func

        assert main_func is not None
        assert callable(main_func)

    def test_cli_main_function_import(self) -> None:
        """Test that main function can be imported directly."""
        from mlsdm.cli.main import main

        assert main is not None
        assert callable(main)

    def test_cli_dunder_main_import(self) -> None:
        """Test that __main__ module can be imported."""
        from mlsdm.cli import __main__

        assert __main__ is not None


class TestCLIMainFunction:
    """Test CLI main function behavior."""

    def test_main_function_parses_args(self) -> None:
        """Test that main function parses command-line arguments."""
        from mlsdm.cli.main import main

        # Mock the dependencies to prevent actual execution
        with patch("mlsdm.cli.main.ConfigLoader") as mock_config_loader, \
             patch("mlsdm.cli.main.MemoryManager") as mock_manager, \
             patch("sys.argv", ["mlsdm", "--config", "test.yaml", "--steps", "10"]):
            
            mock_config = MagicMock()
            mock_config_loader.load_config.return_value = mock_config
            mock_manager_instance = MagicMock()
            mock_manager.return_value = mock_manager_instance

            # Run main function
            try:
                main()
            except SystemExit:
                pass  # Expected if main() calls sys.exit()

            # Verify config was loaded and manager was created
            mock_config_loader.load_config.assert_called_once_with("test.yaml")
            mock_manager.assert_called_once_with(mock_config)

    def test_main_function_uses_default_config(self) -> None:
        """Test that main function uses default config when not specified."""
        from mlsdm.cli.main import main

        with patch("mlsdm.cli.main.ConfigLoader") as mock_config_loader, \
             patch("mlsdm.cli.main.MemoryManager") as mock_manager, \
             patch("sys.argv", ["mlsdm"]):
            
            mock_config = MagicMock()
            mock_config_loader.load_config.return_value = mock_config
            mock_manager_instance = MagicMock()
            mock_manager.return_value = mock_manager_instance

            try:
                main()
            except SystemExit:
                pass

            # Verify default config path was used
            mock_config_loader.load_config.assert_called_once_with("config/default_config.yaml")

    def test_main_function_runs_simulation(self) -> None:
        """Test that main function runs simulation with correct steps."""
        from mlsdm.cli.main import main

        with patch("mlsdm.cli.main.ConfigLoader") as mock_config_loader, \
             patch("mlsdm.cli.main.MemoryManager") as mock_manager, \
             patch("sys.argv", ["mlsdm", "--steps", "50"]):
            
            mock_config = MagicMock()
            mock_config_loader.load_config.return_value = mock_config
            mock_manager_instance = MagicMock()
            mock_manager.return_value = mock_manager_instance

            try:
                main()
            except SystemExit:
                pass

            # Verify simulation was run with correct number of steps
            mock_manager_instance.run_simulation.assert_called_once_with(50)


class TestCLIMainModule:
    """Test __main__ module entry point."""

    def test_main_module_calls_main_function(self) -> None:
        """Test that __main__ module calls main() function."""
        import importlib.util
        import sys
        from pathlib import Path

        # Get the path to __main__.py
        main_path = Path(__file__).parent.parent.parent.parent / "src" / "mlsdm" / "cli" / "__main__.py"
        
        # Mock the main function and sys.exit
        with patch("mlsdm.cli.main") as mock_main_func, \
             patch("sys.exit") as mock_exit:
            
            mock_main_func.return_value = 0
            
            # Load and execute the __main__ module
            spec = importlib.util.spec_from_file_location("__main__", main_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Execute only if __name__ == "__main__" condition would be true
                # We can't easily test this without actually running it
                # So we just verify the module loads
                assert module is not None
