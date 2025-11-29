"""
MLSDM API: FastAPI HTTP API for the MLSDM service.

This module provides HTTP endpoints for text generation, health checks,
and system state management.

## Stable Schemas

For stable, documented API schemas, import from `mlsdm.api.schemas`:
- GenerateRequest, GenerateResponse
- InferRequest, InferResponse
- ErrorResponse, ErrorDetail
- HealthStatus, ReadinessStatus, etc.
"""

from mlsdm.api.schemas import (
    DetailedHealthStatus,
    ErrorDetail,
    ErrorResponse,
    EventInput,
    GenerateRequest,
    GenerateResponse,
    GenerateResponseDTO,
    HealthStatus,
    InferRequest,
    InferResponse,
    ReadinessStatus,
    SimpleHealthStatus,
    StateResponse,
)

__all__ = [
    # Request schemas
    "GenerateRequest",
    "InferRequest",
    "EventInput",
    # Response schemas
    "GenerateResponse",
    "GenerateResponseDTO",
    "InferResponse",
    "StateResponse",
    # Health schemas
    "SimpleHealthStatus",
    "HealthStatus",
    "ReadinessStatus",
    "DetailedHealthStatus",
    # Error schemas
    "ErrorDetail",
    "ErrorResponse",
]
