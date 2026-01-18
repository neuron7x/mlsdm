from __future__ import annotations

from mlsdm.api.app import create_app


def test_api_middleware_order_contract() -> None:
    app = create_app()
    middleware_order = [middleware.cls.__name__ for middleware in app.user_middleware]

    assert middleware_order == [
        "BulkheadMiddleware",
        "PriorityMiddleware",
        "TimeoutMiddleware",
        "RequestIDMiddleware",
        "SecurityHeadersMiddleware",
    ]
