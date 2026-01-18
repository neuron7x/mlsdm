from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from mlsdm.api.middleware import PriorityMiddleware, RequestIDMiddleware
from mlsdm.contracts.request_state import UNKNOWN_REQUEST_ID, snapshot_request_state


def test_request_state_contract_snapshot() -> None:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(PriorityMiddleware)

    @app.get("/state")
    async def state(request: Request) -> dict[str, object]:
        snapshot = snapshot_request_state(request)
        return {
            "request_id": snapshot.request_id,
            "priority": snapshot.priority,
            "priority_weight": snapshot.priority_weight,
            "user_info_is_none": snapshot.user_info is None,
            "user_context_is_none": snapshot.user_context is None,
            "client_cert_is_none": snapshot.client_cert is None,
        }

    client = TestClient(app)
    response = client.get("/state", headers={"X-MLSDM-Priority": "high"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"]
    assert payload["request_id"] != UNKNOWN_REQUEST_ID
    assert payload["priority"] == "high"
    assert payload["priority_weight"] == 3
    assert payload["user_info_is_none"] is True
    assert payload["user_context_is_none"] is True
    assert payload["client_cert_is_none"] is True
