import pytest
from pydantic import ValidationError

from mlsdm.api.schemas import (
    CognitiveStateResponse,
    ErrorResponse,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    ReadinessResponse,
)


def test_generate_request_validates_bounds() -> None:
    request = GenerateRequest(prompt="hello", moral_value=0.5, max_tokens=128)
    assert request.prompt == "hello"
    assert request.moral_value == 0.5
    assert request.max_tokens == 128

    with pytest.raises(ValidationError):
        GenerateRequest(prompt="", moral_value=0.5)

    with pytest.raises(ValidationError):
        GenerateRequest(prompt="ok", moral_value=1.5)

    with pytest.raises(ValidationError):
        GenerateRequest(prompt="ok", max_tokens=0)


def test_generate_response_requires_contract_fields() -> None:
    response = GenerateResponse(
        response="text",
        accepted=True,
        phase="wake",
        moral_score=0.42,
        emergency_shutdown=False,
        cognitive_state=CognitiveStateResponse(
            phase="wake",
            stateless_mode=False,
            emergency_shutdown=False,
            memory_used_mb=12.5,
            moral_threshold=0.7,
        ),
    )
    assert response.response == "text"
    assert response.cognitive_state is not None

    with pytest.raises(ValidationError):
        GenerateResponse(response="text", accepted=True)


def test_health_and_readiness_schemas_enforce_contract() -> None:
    health = HealthResponse(status="ok")
    assert health.emergency_shutdown is False

    readiness = ReadinessResponse(ready=True)
    assert readiness.details == {}

    with pytest.raises(ValidationError):
        HealthResponse(status="unknown")


def test_error_response_contract_fields() -> None:
    error = ErrorResponse(error_code="rate_limit_exceeded", message="Too many requests")
    assert error.debug_id is None
