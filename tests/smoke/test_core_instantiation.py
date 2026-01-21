"""Tier 1 Smoke: Core component instantiation tests."""
import pytest

pytestmark = pytest.mark.smoke


class TestCoreInstantiation:
    """Verify core components can be instantiated with defaults."""

    def test_cognitive_controller_default_init(self):
        from mlsdm.core.cognitive_controller import CognitiveController
        controller = CognitiveController()
        assert controller is not None
        assert hasattr(controller, 'process_event')

    def test_config_loading(self):
        """Verify default configuration loads without errors."""
        import yaml
        from pathlib import Path

        config_path = Path("config/default_config.yaml")
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            assert isinstance(config, dict)
