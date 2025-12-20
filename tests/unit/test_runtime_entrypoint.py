from types import SimpleNamespace

import pytest

from mlsdm.api.app import app as canonical_app
from mlsdm.entrypoints import serve as serve_entrypoint
from mlsdm.service.neuro_engine_service import create_app


def test_canonical_app_factory_is_single_source():
    assert serve_entrypoint.get_canonical_app() is canonical_app
    assert create_app() is canonical_app


def test_cli_serve_delegates_to_canonical_runtime(monkeypatch):
    called: dict[str, object] = {}

    def fake_serve(**kwargs):
        called.update(kwargs)
        return 0

    monkeypatch.setattr("mlsdm.entrypoints.serve.serve", fake_serve)

    from mlsdm.cli import cmd_serve

    args = SimpleNamespace(
        host="0.0.0.0",
        port=9000,
        log_level="info",
        reload=False,
        config=None,
        backend=None,
        disable_rate_limit=False,
    )

    result = cmd_serve(args)

    assert result == 0
    assert called["host"] == "0.0.0.0"
    assert called["port"] == 9000
    assert called["log_level"] == "info"
    assert called["reload"] is False
