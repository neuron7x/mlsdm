"""
Standardized API Error Models for MLSDM.

This module provides standardized error response models for all API endpoints,
ensuring consistent error handling and response format across the application.

CONTRACT STABILITY:
- ApiError and ApiErrorResponse are part of the stable API contract.
- Do not modify field names or types without a major version bump.
- New optional fields can be added to ApiError.details.

Usage:
    from mlsdm.contracts.errors import ApiError, ApiErrorResponse

    error = ApiError(code="validation_error", message="Invalid input")
    response = ApiErrorResponse(error=error)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    """Standardized API error model.

    CONTRACT: This model is part of the stable API contract.
    All API error responses must use this structure.

    Attributes:
        code: Machine-readable error code (e.g., 'validation_error', 'rate_limit_exceeded').
        message: Human-readable error message for display/logging.
        details: Optional dictionary with additional error context.

    Example codes:
        - validation_error: Input validation failed
        - rate_limit_exceeded: Client exceeded rate limit
        - internal_error: Unexpected server error
        - unauthorized: Missing or invalid authentication
        - dimension_mismatch: Vector dimension does not match expected
        - moral_value_out_of_range: Moral value outside [0.0, 1.0]
    """

    code: str = Field(
        ...,
        description="Machine-readable error code",
        json_schema_extra={"examples": ["validation_error", "rate_limit_exceeded"]},
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        json_schema_extra={"examples": ["Prompt cannot be empty"]},
    )
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error context (field-specific info, constraints violated, etc.)",
    )


class ApiErrorResponse(BaseModel):
    """Wrapper for API error responses.

    CONTRACT: All error responses MUST use this wrapper structure.
    This ensures consistent error handling in client code.

    The response body for any 4xx/5xx response will be:
        {"error": {"code": "...", "message": "...", "details": ...}}
    """

    error: ApiError = Field(
        description="Error details following the ApiError schema"
    )
