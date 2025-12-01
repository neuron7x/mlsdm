"""
MLSDM API Contracts Module.

This module provides strictly typed Pydantic models for all API endpoints,
ensuring consistent validation, serialization, and documentation.

CONTRACT STABILITY:
- All models marked as "Contract" are part of the public API contract.
- Breaking changes require a major version bump.
- New fields can be added but existing fields should not be removed/renamed.

Modules:
- event_models: Models for /v1/process_event/ and /v1/state/ endpoints
- errors: Standardized API error response models
"""

from mlsdm.contracts.errors import ApiError, ApiErrorResponse
from mlsdm.contracts.event_models import (
    EventInput,
    StateResponse,
)

__all__ = [
    # Event models
    "EventInput",
    "StateResponse",
    # Error models
    "ApiError",
    "ApiErrorResponse",
]
