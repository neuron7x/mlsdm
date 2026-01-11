"""
Neuro-signal and control-loop contract models.

These models define stable signal interfaces for risk assessment, reward
prediction error, action gating, lifecycle hooks, stability metrics, and
latency requirements.

CONTRACT STABILITY:
These models are part of the stable internal API contract.
Do not modify field names or types without a major version bump.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RiskSignal(BaseModel):
    """Normalized risk/threat signal for control-loop gating."""

    threat: float = Field(0.0, ge=0.0, le=1.0, description="Threat signal in [0,1].")
    risk: float = Field(0.0, ge=0.0, le=1.0, description="Risk signal in [0,1].")
    source: str | None = Field(default=None, description="Optional origin of the signal.")
    metadata: dict[str, float | int | str] = Field(
        default_factory=dict,
        description="Additional normalized risk metadata.",
    )


class RewardPredictionErrorSignal(BaseModel):
    """Reward prediction error (RPE) signal emitted by learning dynamics."""

    delta: list[float] = Field(default_factory=list, description="Raw prediction error delta per dimension.")
    abs_delta: float = Field(0.0, ge=0.0, description="Mean absolute delta magnitude.")
    clipped_delta: list[float] = Field(default_factory=list, description="Clipped delta values.")
    components: list[float] = Field(default_factory=list, description="Per-dimension absolute components.")
    reward: float | None = Field(default=None, description="Observed reward associated with RPE.")


class ActionGatingSignal(BaseModel):
    """Action gating signal describing whether an action may proceed."""

    allow: bool = Field(..., description="Whether action execution is allowed.")
    reason: str = Field(default="", description="Primary gating reason.")
    mode: str | None = Field(default=None, description="Risk mode or regime state.")
    metadata: dict[str, float | int | str | bool] = Field(
        default_factory=dict,
        description="Additional gating metadata (e.g., stage, audit tags).",
    )


class StabilityMetrics(BaseModel):
    """Stability metrics for adaptive control loops."""

    max_abs_delta: float = Field(0.0, ge=0.0)
    windowed_max_abs_delta: float = Field(0.0, ge=0.0)
    oscillation_index: float = Field(0.0, ge=0.0)
    sign_flip_rate: float = Field(0.0, ge=0.0)
    regime_flip_rate: float = Field(0.0, ge=0.0)
    convergence_time: float = Field(-1.0, description="Time to converge, -1 if not converged.")
    instability_events_count: int = Field(0, ge=0)
    time_to_kill_switch: int | None = Field(default=None, description="Steps to kill switch trigger.")
    recovered: bool = Field(default=False)


class LifecycleHook(BaseModel):
    """Lifecycle hook contract for pre/post stages."""

    component: str = Field(..., description="Component or pipeline stage name.")
    phase: Literal["pre", "post"] = Field(..., description="Hook phase.")
    hook: str = Field(..., description="Hook identifier.")
    description: str | None = Field(default=None, description="Optional hook description.")


class LatencyRequirement(BaseModel):
    """Latency requirement contract for stages or pipelines."""

    stage: str = Field(..., description="Stage identifier.")
    target_ms: float = Field(..., ge=0.0, description="Target latency in ms.")
    warn_ms: float | None = Field(default=None, ge=0.0, description="Warning threshold in ms.")
    hard_limit_ms: float | None = Field(default=None, ge=0.0, description="Hard maximum latency in ms.")


class LatencyProfile(BaseModel):
    """Latency requirement profile for end-to-end execution."""

    total_budget_ms: float = Field(..., ge=0.0, description="Total latency budget in ms.")
    stages: list[LatencyRequirement] = Field(default_factory=list, description="Per-stage latency budgets.")
