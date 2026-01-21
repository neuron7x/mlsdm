"""Tier 1 Smoke: Critical import path validation."""
import pytest

pytestmark = pytest.mark.smoke


class TestCoreImports:
    """Verify all critical modules are importable."""

    def test_cognitive_controller_import(self):
        from mlsdm.core.cognitive_controller import CognitiveController
        assert CognitiveController is not None

    def test_neuro_engine_import(self):
        from mlsdm.engine.neuro_cognitive_engine import NeuroCognitiveEngine
        assert NeuroCognitiveEngine is not None

    def test_api_middleware_imports(self):
        from mlsdm.api.middleware import BulkheadMiddleware, TimeoutMiddleware
        assert BulkheadMiddleware is not None
        assert TimeoutMiddleware is not None

    def test_security_rbac_imports(self):
        from mlsdm.security.rbac import RBACMiddleware, Role, RoleValidator
        assert RBACMiddleware is not None
        assert Role is not None

    def test_observability_imports(self):
        from mlsdm.observability.logger import ObservabilityLogger
        from mlsdm.observability.metrics import MetricsExporter
        assert ObservabilityLogger is not None
        assert MetricsExporter is not None
