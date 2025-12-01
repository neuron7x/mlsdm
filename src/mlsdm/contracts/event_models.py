"""
Event API Contract Models for MLSDM.

This module provides strictly typed Pydantic models for the /v1/process_event/
and /v1/state/ endpoints, ensuring proper validation and documentation.

CONTRACT STABILITY:
- EventInput and StateResponse are part of the stable API contract.
- Do not modify field names or types without a major version bump.
- New optional fields can be added.

Usage:
    from mlsdm.contracts.event_models import EventInput, StateResponse

    # Validate input
    event = EventInput(event_vector=[0.1, 0.2, ...], moral_value=0.8)

    # Build response
    response = StateResponse(
        L1_norm=1.5,
        L2_norm=2.3,
        L3_norm=0.8,
        current_phase="wake",
        ...
    )
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EventInput(BaseModel):
    """Request model for /v1/process_event/ endpoint.

    CONTRACT: These fields are part of the stable API contract.
    Do not modify without a major version bump.

    Attributes:
        event_vector: Embedding vector for the cognitive event.
            Must be a list of floats with dimension matching the system configuration.
            Default dimension is 384 (configurable via CONFIG_PATH).
        moral_value: Moral score for the event in range [0.0, 1.0].
            Events below the adaptive moral threshold will be rejected.

    Validation:
        - event_vector: Non-empty list of finite floats
        - moral_value: Float in range [0.0, 1.0]

    Example:
        {
            "event_vector": [0.1, 0.2, -0.1, ...],  // 384-dimensional vector
            "moral_value": 0.75
        }
    """

    event_vector: list[float] = Field(
        ...,
        min_length=1,
        description=(
            "Embedding vector for the cognitive event. "
            "Must match the configured embedding dimension (default: 384)."
        ),
        json_schema_extra={
            "examples": [[0.1, 0.2, -0.1, 0.3]],  # Abbreviated example
        },
    )
    moral_value: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Moral score for the event. Range: [0.0, 1.0].",
        json_schema_extra={"examples": [0.75]},
    )

    @field_validator("event_vector")
    @classmethod
    def validate_vector_values(cls, v: list[float]) -> list[float]:
        """Validate that all vector values are finite (not NaN or Inf)."""
        import math

        for i, val in enumerate(v):
            if not math.isfinite(val):
                raise ValueError(
                    f"event_vector[{i}] contains non-finite value: {val}. "
                    "All values must be finite floats."
                )
        return v


class StateResponse(BaseModel):
    """Response model for /v1/state/ and /v1/process_event/ endpoints.

    CONTRACT: These fields are part of the stable API contract.
    Do not modify without a major version bump.

    Provides a snapshot of the cognitive system state including:
    - Memory layer norms (L1/L2/L3 synaptic memory)
    - Current cognitive phase (wake/sleep)
    - Event processing statistics
    - Moral filter threshold

    Attributes:
        L1_norm: Euclidean norm of L1 (working) memory layer.
        L2_norm: Euclidean norm of L2 (short-term) memory layer.
        L3_norm: Euclidean norm of L3 (long-term) memory layer.
        current_phase: Current cognitive rhythm phase ("wake" or "sleep").
        latent_events_count: Number of events in latent/pending state.
        accepted_events_count: Total events accepted by moral filter.
        total_events_processed: Total events processed (accepted + rejected).
        moral_filter_threshold: Current adaptive moral filter threshold [0.0, 1.0].

    Example:
        {
            "L1_norm": 1.5,
            "L2_norm": 2.3,
            "L3_norm": 0.8,
            "current_phase": "wake",
            "latent_events_count": 10,
            "accepted_events_count": 85,
            "total_events_processed": 100,
            "moral_filter_threshold": 0.5
        }
    """

    L1_norm: float = Field(
        ...,
        ge=0.0,
        description="Euclidean norm of L1 (working) memory layer.",
        json_schema_extra={"examples": [1.5]},
    )
    L2_norm: float = Field(
        ...,
        ge=0.0,
        description="Euclidean norm of L2 (short-term) memory layer.",
        json_schema_extra={"examples": [2.3]},
    )
    L3_norm: float = Field(
        ...,
        ge=0.0,
        description="Euclidean norm of L3 (long-term) memory layer.",
        json_schema_extra={"examples": [0.8]},
    )
    current_phase: Literal["wake", "sleep"] = Field(
        ...,
        description="Current cognitive rhythm phase.",
        json_schema_extra={"examples": ["wake"]},
    )
    latent_events_count: int = Field(
        ...,
        ge=0,
        description="Number of events in latent/pending state.",
        json_schema_extra={"examples": [10]},
    )
    accepted_events_count: int = Field(
        ...,
        ge=0,
        description="Total events accepted by moral filter.",
        json_schema_extra={"examples": [85]},
    )
    total_events_processed: int = Field(
        ...,
        ge=0,
        description="Total events processed (accepted + rejected).",
        json_schema_extra={"examples": [100]},
    )
    moral_filter_threshold: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Current adaptive moral filter threshold.",
        json_schema_extra={"examples": [0.5]},
    )
