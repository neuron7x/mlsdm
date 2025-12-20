from fastapi import FastAPI

from mlsdm.serve import get_app


def test_get_app_api_returns_fastapi() -> None:
    app = get_app("api")
    assert isinstance(app, FastAPI)
    assert any("/health" in route.path for route in app.router.routes)


def test_get_app_neuro_returns_fastapi() -> None:
    app = get_app("neuro")
    assert isinstance(app, FastAPI)
    assert any(route.path == "/v1/neuro/generate" for route in app.router.routes)
