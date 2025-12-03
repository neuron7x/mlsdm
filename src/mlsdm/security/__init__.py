"""
MLSDM Security: Security utilities for the NeuroCognitiveEngine.

This module provides security features including rate limiting,
payload scrubbing, RBAC, prompt injection detection, and logging controls.
"""

from mlsdm.security.payload_scrubber import (
    DEFAULT_SECRET_KEYS,
    EMAIL_PATTERN,
    FORBIDDEN_FIELDS,
    PII_FIELDS,
    SECRET_PATTERNS,
    is_secure_mode,
    scrub_dict,
    scrub_log_record,
    scrub_request_payload,
    scrub_text,
    should_log_payload,
)
from mlsdm.security.prompt_injection import (
    DetectionResult,
    PromptInjectionDetector,
    RiskLevel,
    check_prompt_injection,
    get_prompt_injection_detector,
)
from mlsdm.security.rate_limit import RateLimiter, get_rate_limiter
from mlsdm.security.rbac import (
    Role,
    RoleValidator,
    UserContext,
    get_role_validator,
    require_role,
)

__all__ = [
    # Rate limiting
    "RateLimiter",
    "get_rate_limiter",
    # Payload scrubbing
    "scrub_text",
    "scrub_dict",
    "scrub_request_payload",
    "scrub_log_record",
    "should_log_payload",
    "is_secure_mode",
    "SECRET_PATTERNS",
    "PII_FIELDS",
    "FORBIDDEN_FIELDS",
    "EMAIL_PATTERN",
    "DEFAULT_SECRET_KEYS",
    # RBAC
    "Role",
    "RoleValidator",
    "UserContext",
    "get_role_validator",
    "require_role",
    # Prompt injection
    "PromptInjectionDetector",
    "DetectionResult",
    "RiskLevel",
    "check_prompt_injection",
    "get_prompt_injection_detector",
]
