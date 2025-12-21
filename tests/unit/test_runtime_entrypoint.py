from types import SimpleNamespace

from mlsdm.api.app import app as canonical_app
from mlsdm.service.neuro_engine_service import create_app
from mlsdm.serve import get_app


def test_canonical_app_factory_is_single_source():
    app_from_service = create_app()
    app_from_serve = get_app("api")

    # All factories must surface the same canonical instance
    assert app_from_service is canonical_app
    assert app_from_serve is canonical_app


def test_cli_serve_delegates_to_canonical_runtime(monkeypatch):
    called: dict[str, object] = {}

    def fake_run(**kwargs):
        called.update(kwargs)
        return 0

    monkeypatch.setattr("mlsdm.serve.run_server", fake_run)

    from mlsdm.cli import cmd_serve

    args = SimpleNamespace(
        host="0.0.0.0",
        port=9000,
        log_level="info",
        reload=False,
        config=None,
        backend=None,
        disable_rate_limit=False,
        mode="api",
    )

    result = cmd_serve(args)

    assert result == 0
    assert called["host"] == "0.0.0.0"
    assert called["port"] == 9000
    assert called["log_level"] == "info"
    assert called["reload"] is False
