"""Security Integration for MLSDM API.

This module provides helper functions to integrate security features
(policy engine, guardrails, LLM safety) into API endpoints and pipelines.

These functions bridge the runtime configuration with security modules,
making it easy to conditionally apply security checks based on the
deployment mode.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from mlsdm.config_runtime import get_runtime_config

if TYPE_CHECKING:
    from fastapi import Request
    from mlsdm.security.policy_engine import PolicyContext, PolicyDecision
    from mlsdm.security.guardrails import GuardrailResult

logger = logging.getLogger(__name__)


def create_policy_context_from_request(
    request: Request,
    route: str,
    prompt: str | None = None,
    response: str | None = None,
    **kwargs: Any
) -> PolicyContext:
    """Create a PolicyContext from a FastAPI request.
    
    Args:
        request: FastAPI request object
        route: API route (e.g., "/generate")
        prompt: User prompt (for LLM operations)
        response: LLM response (for output filtering)
        **kwargs: Additional context metadata
        
    Returns:
        PolicyContext for policy evaluation
    """
    from mlsdm.security.policy_engine import PolicyContext
    
    # Extract user info from request state (set by OIDC/mTLS middleware)
    user_id = getattr(request.state, "user_id", None)
    user_roles = getattr(request.state, "user_roles", [])
    tenant_id = getattr(request.state, "tenant_id", None)
    client_id = getattr(request.state, "client_id", "unknown")
    
    # Extract authentication flags
    has_valid_token = getattr(request.state, "has_valid_token", False)
    has_valid_signature = getattr(request.state, "has_valid_signature", False)
    has_mtls_cert = getattr(request.state, "has_mtls_cert", False)
    
    # Calculate payload size
    payload_size = len(prompt.encode()) if prompt else 0
    if response:
        payload_size += len(response.encode())
    
    # Build context
    context = PolicyContext(
        user_id=user_id,
        user_roles=user_roles,
        client_id=client_id,
        has_valid_token=has_valid_token,
        has_valid_signature=has_valid_signature,
        has_mtls_cert=has_mtls_cert,
        route=route,
        method=request.method,
        payload_size=payload_size,
        request_headers={k: v for k, v in request.headers.items()},
        prompt=prompt,
        response=response,
        metadata={
            "tenant_id": tenant_id,
            "request_id": getattr(request.state, "request_id", None),
            **kwargs
        }
    )
    
    return context


def evaluate_request_policy_if_enabled(
    context: PolicyContext,
) -> PolicyDecision | None:
    """Evaluate request policy if policy engine is enabled.
    
    Args:
        context: Policy evaluation context
        
    Returns:
        PolicyDecision if policy engine is enabled, None otherwise
    """
    config = get_runtime_config()
    
    if not config.security.enable_policy_engine:
        # Policy engine disabled, allow by default
        return None
    
    logger.debug(f"Evaluating policy for route={context.route}, user={context.user_id}")
    
    from mlsdm.security.policy_engine import evaluate_request_policy
    from mlsdm.utils.security_logger import get_security_logger
    
    decision = evaluate_request_policy(context)
    
    # Log policy decision
    security_logger = get_security_logger()
    if not decision.allow:
        security_logger.log_policy_violation(
            client_id=context.client_id,
            policy=decision.policy_name or "unknown",
            reason=decision.reasons[0] if decision.reasons else "Policy denied"
        )
    
    return decision


def apply_guardrails_if_enabled(
    prompt: str | None = None,
    response: str | None = None,
    context: dict[str, Any] | None = None,
) -> GuardrailResult | None:
    """Apply LLM guardrails if enabled.
    
    Args:
        prompt: User prompt (for input guardrails)
        response: LLM response (for output guardrails)
        context: Additional context metadata
        
    Returns:
        GuardrailResult if guardrails are enabled, None otherwise
    """
    config = get_runtime_config()
    
    if not config.security.enable_guardrails:
        # Guardrails disabled
        return None
    
    logger.debug("Applying guardrails to request/response")
    
    from mlsdm.security.guardrails import (
        enforce_request_guardrails,
        enforce_response_guardrails,
    )
    
    if prompt and not response:
        # Input guardrails
        return enforce_request_guardrails(prompt, context or {})
    elif response:
        # Output guardrails
        return enforce_response_guardrails(response, context or {})
    
    return None


def analyze_llm_safety_if_enabled(
    text: str,
    is_prompt: bool = True,
) -> dict[str, Any] | None:
    """Analyze LLM safety if enabled.
    
    Args:
        text: Text to analyze (prompt or response)
        is_prompt: True if analyzing prompt, False if analyzing response
        
    Returns:
        Safety analysis result if LLM safety is enabled, None otherwise
    """
    config = get_runtime_config()
    
    if not config.security.enable_llm_safety:
        # LLM safety disabled
        return None
    
    logger.debug(f"Analyzing LLM safety for {'prompt' if is_prompt else 'response'}")
    
    from mlsdm.security.llm_safety import analyze_prompt, filter_output
    
    if is_prompt:
        result = analyze_prompt(text)
        return {
            "risk_level": result.risk_level.value,
            "flags": result.flags,
            "violations": result.violations,
            "blocked": result.should_block,
        }
    else:
        result = filter_output(text)
        return {
            "risk_level": result.risk_level.value,
            "flags": result.flags,
            "violations": result.violations,
            "blocked": result.should_block,
            "filtered_output": result.filtered_output,
        }


def check_multi_tenant_enforcement(
    request: Request,
    resource_tenant_id: str | None = None,
) -> bool:
    """Check multi-tenant enforcement if enabled.
    
    Args:
        request: FastAPI request object
        resource_tenant_id: Tenant ID of the resource being accessed
        
    Returns:
        True if access is allowed, False otherwise
    """
    config = get_runtime_config()
    
    if not config.security.enable_multi_tenant_enforcement:
        # Multi-tenant enforcement disabled
        return True
    
    # Get user's tenant from request state
    user_tenant_id = getattr(request.state, "tenant_id", None)
    
    # If resource_tenant_id is provided, verify it matches user's tenant
    if resource_tenant_id and user_tenant_id:
        if resource_tenant_id != user_tenant_id:
            logger.warning(
                f"Tenant mismatch: user_tenant={user_tenant_id}, "
                f"resource_tenant={resource_tenant_id}"
            )
            return False
    
    return True
