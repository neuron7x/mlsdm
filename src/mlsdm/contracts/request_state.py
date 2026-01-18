"""Request state contract shared across middleware and security layers.

Invariants:
- request.state contains a stable set of attributes for downstream consumers.
- request_id is always a non-empty string once RequestIDMiddleware runs.
- priority/priority_weight are set together when priority parsing is enabled.
- security middleware must set user_info, user_context, and client_cert explicitly,
  even when unauthenticated (set to None).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request

    from mlsdm.security.mtls import ClientCertInfo
    from mlsdm.security.oidc import UserInfo
    from mlsdm.security.rbac import UserContext


REQUEST_STATE_FIELDS: tuple[str, ...] = (
    "request_id",
    "priority",
    "priority_weight",
    "user_info",
    "user_context",
    "client_cert",
)

UNKNOWN_REQUEST_ID = "unknown"


@dataclass(frozen=True)
class RequestStateSnapshot:
    """Snapshot of request.state values for contract validation."""

    request_id: str | None
    priority: str | None
    priority_weight: int | None
    user_info: UserInfo | None
    user_context: UserContext | None
    client_cert: ClientCertInfo | None


def ensure_request_state(request: Request) -> None:
    """Ensure request.state has all known attributes set.

    This does not overwrite existing values; it only creates missing attributes
    with a None value to make state propagation explicit and deterministic.
    """
    for field_name in REQUEST_STATE_FIELDS:
        if not hasattr(request.state, field_name):
            setattr(request.state, field_name, None)


def set_request_id(request: Request, request_id: str) -> None:
    """Set request_id on the request state.

    Raises:
        ValueError: If request_id is not a non-empty string.
    """
    if not isinstance(request_id, str) or not request_id:
        raise ValueError("request_id must be a non-empty string")
    ensure_request_state(request)
    request.state.request_id = request_id


def set_request_priority(request: Request, priority: str, weight: int) -> None:
    """Set priority fields on the request state.

    Raises:
        ValueError: If priority is not a string or weight is not an int.
    """
    if not isinstance(priority, str):
        raise ValueError("priority must be a string")
    if not isinstance(weight, int):
        raise ValueError("priority_weight must be an int")
    ensure_request_state(request)
    request.state.priority = priority
    request.state.priority_weight = weight


def set_request_user_info(request: Request, user_info: UserInfo | None) -> None:
    """Set user_info on the request state."""
    ensure_request_state(request)
    request.state.user_info = user_info


def set_request_user_context(request: Request, user_context: UserContext | None) -> None:
    """Set user_context on the request state."""
    ensure_request_state(request)
    request.state.user_context = user_context


def set_request_client_cert(request: Request, client_cert: ClientCertInfo | None) -> None:
    """Set client_cert on the request state."""
    ensure_request_state(request)
    request.state.client_cert = client_cert


def get_request_id(request: Request) -> str:
    """Return request_id or UNKNOWN_REQUEST_ID if missing."""
    ensure_request_state(request)
    request_id = request.state.request_id
    if isinstance(request_id, str) and request_id:
        return request_id
    return UNKNOWN_REQUEST_ID


def get_request_user_info(request: Request) -> UserInfo | None:
    """Return user_info from request state."""
    ensure_request_state(request)
    return request.state.user_info


def get_request_user_context(request: Request) -> UserContext | None:
    """Return user_context from request state."""
    ensure_request_state(request)
    return request.state.user_context


def get_request_client_cert(request: Request) -> ClientCertInfo | None:
    """Return client_cert from request state."""
    ensure_request_state(request)
    return request.state.client_cert


def snapshot_request_state(request: Request) -> RequestStateSnapshot:
    """Create a snapshot of request.state for contract validation."""
    ensure_request_state(request)
    return RequestStateSnapshot(
        request_id=request.state.request_id,
        priority=request.state.priority,
        priority_weight=request.state.priority_weight,
        user_info=request.state.user_info,
        user_context=request.state.user_context,
        client_cert=request.state.client_cert,
    )


__all__ = [
    "REQUEST_STATE_FIELDS",
    "UNKNOWN_REQUEST_ID",
    "RequestStateSnapshot",
    "ensure_request_state",
    "set_request_id",
    "set_request_priority",
    "set_request_user_info",
    "set_request_user_context",
    "set_request_client_cert",
    "get_request_id",
    "get_request_user_info",
    "get_request_user_context",
    "get_request_client_cert",
    "snapshot_request_state",
]
