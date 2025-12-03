# Security Features Quick Start

## Overview

The MLSDM Governed Cognitive Memory system includes comprehensive security features:

✅ **API Authentication & RBAC** - Role-based access control with API keys  
✅ **Rate Limiting** - 5 RPS per client  
✅ **Input Validation** - Comprehensive validation and sanitization  
✅ **LLM Safety** - Prompt injection detection and moral filtering  
✅ **Security Logging** - Structured audit logs with correlation IDs  
✅ **Dependency Scanning** - Automated vulnerability detection (pip-audit)  
✅ **SAST** - Static Application Security Testing (Bandit/Semgrep)  
✅ **SBOM** - Software Bill of Materials generation on release  
✅ **185+ Security Tests** - All passing  

---

## Security Gap Analysis

| Area                   | Current Status                    | Gaps / TODOs                         |
|------------------------|-----------------------------------|--------------------------------------|
| API Auth & RBAC        | ✅ Implemented                    | Optional: OAuth2/OIDC (SEC-004)      |
| TLS / mTLS             | ✅ Documented (ingress config)    | mTLS for service-mesh (SEC-006)      |
| Secrets Management     | ✅ Env-based, rotation support    | Vault integration (optional)         |
| LLM Safety             | ✅ Prompt injection + moral filter| Advanced context sanitization        |
| Supply Chain (deps)    | ✅ pip-audit in CI                | None                                 |
| SAST                   | ✅ Bandit + Semgrep workflows     | None                                 |
| SBOM                   | ✅ Generated on release           | None                                 |

---

## Quick Start

### Run Security Tests

```bash
# All security tests (185+ tests)
python -m pytest tests/security/ -v --no-cov

# Integration test suite
python scripts/test_security_features.py
```

### Run Security Audit

```bash
# Scan for vulnerabilities
python scripts/security_audit.py

# Scan and attempt fixes
python scripts/security_audit.py --fix

# Generate report
python scripts/security_audit.py --report security_report.txt
```

### Generate SBOM

```bash
# Generate Software Bill of Materials
python scripts/generate_sbom.py --output sbom.json
```

### Configuration

```bash
# Set API key for authentication (required for production)
export API_KEY="your-secure-key-here"

# Set admin API key for administrative endpoints
export ADMIN_API_KEY="your-admin-key-here"

# Enable secure mode for production (disables training, enables scrubbing)
export MLSDM_SECURE_MODE=1

# Disable rate limiting for testing only
export DISABLE_RATE_LIMIT=1
```

---

## Using Security Features

### RBAC (Role-Based Access Control)

```python
from mlsdm.security.rbac import (
    RoleValidator, Role, require_role, get_role_validator
)

# Add API keys with roles
validator = get_role_validator()
validator.add_key("user-key-123", [Role.READ], "user-1")
validator.add_key("admin-key-456", [Role.ADMIN], "admin-1")

# Use decorator for endpoint protection
@require_role(["admin"])
async def admin_only_endpoint(request: Request):
    return {"status": "admin access granted"}
```

### Prompt Injection Detection

```python
from mlsdm.security.prompt_injection import check_prompt_injection

# Check input for injection attempts
result = check_prompt_injection("Ignore all previous instructions")
if result.should_block:
    return {"error": "Request blocked for security reasons"}

print(f"Risk Level: {result.risk_level}")
print(f"Patterns Matched: {result.patterns_matched}")
```

### Rate Limiting

```python
from mlsdm.utils.rate_limiter import RateLimiter

limiter = RateLimiter(rate=5.0, capacity=10)
if limiter.is_allowed(client_id):
    # Process request
    pass
else:
    # Return 429 Too Many Requests
    pass
```

### Input Validation

```python
from mlsdm.utils.input_validator import InputValidator

validator = InputValidator()

# Validate vector
vector = validator.validate_vector([1.0, 2.0, 3.0], expected_dim=3)

# Validate moral value
moral = validator.validate_moral_value(0.75)

# Sanitize string
safe_text = validator.sanitize_string(user_input, max_length=1000)
```

### Security Logging

```python
from mlsdm.utils.security_logger import get_security_logger

logger = get_security_logger()

# Log authentication
logger.log_auth_success(client_id="abc123")
logger.log_auth_failure(client_id="abc123", reason="Invalid token")

# Log RBAC denial
logger.log_rbac_deny(
    client_id="abc123",
    user_id="user-1",
    required_roles=["admin"],
    user_roles=["read"],
    path="/admin/reset"
)

# Log prompt injection detection
logger.log_prompt_injection_detected(
    client_id="abc123",
    risk_level="high",
    patterns_matched=["ignore_instructions"],
    blocked=True
)

# Log moral filter block
logger.log_moral_filter_block(
    client_id="abc123",
    moral_score=0.2,
    threshold=0.5
)
```

---

## API Endpoints

All endpoints include rate limiting and input validation:

```bash
# Health check (no auth required)
curl http://localhost:8000/health

# Get state (requires auth - read role)
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/v1/state/

# Generate response (requires auth - write role)
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello, how are you?"}' \
     http://localhost:8000/generate

# Process event (requires auth - write role, rate limited, validated)
curl -X POST -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"event_vector": [1.0, 2.0, 3.0], "moral_value": 0.8}' \
     http://localhost:8000/v1/process_event/
```

---

## Secrets Management

### Environment Variables

| Variable             | Description                         | Required |
|----------------------|-------------------------------------|----------|
| `API_KEY`            | Default API key (write role)        | Yes (prod) |
| `ADMIN_API_KEY`      | Admin API key (admin role)          | No       |
| `MLSDM_SECURE_MODE`  | Enable secure mode (1/true)         | Yes (prod) |
| `OPENAI_API_KEY`     | OpenAI API key (if using OpenAI)    | Depends  |

### Secret Rotation

To rotate API keys without downtime:

1. Add new key to environment/Kubernetes Secret
2. Update deployment (rolling update)
3. Wait for all pods to pick up new key
4. Remove old key from configuration
5. Verify via health check

```bash
# Example: Update Kubernetes Secret
kubectl create secret generic mlsdm-secrets \
  --from-literal=API_KEY=new-key-value \
  --from-literal=OLD_API_KEY=old-key-value \
  --dry-run=client -o yaml | kubectl apply -f -

# Rolling restart to pick up new secrets
kubectl rollout restart deployment/mlsdm-api
```

---

## TLS Configuration

### HTTPS via Ingress

The MLSDM API is designed to run behind a TLS-terminating ingress:

```yaml
# deploy/k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
    - hosts:
        - mlsdm-api.example.com
      secretName: mlsdm-tls-certificate
```

### mTLS (Service-to-Service)

For mTLS between services, use a service mesh (Istio, Linkerd) or direct certificate configuration. See `DEPLOYMENT_GUIDE.md` for details.

---

## Documentation

- **Full Implementation Guide:** [SECURITY_IMPLEMENTATION.md](SECURITY_IMPLEMENTATION.md)
- **Validation Report:** [SECURITY_SUMMARY.md](SECURITY_SUMMARY.md)
- **Security Policy:** [SECURITY_POLICY.md](SECURITY_POLICY.md)
- **Threat Model:** [THREAT_MODEL.md](THREAT_MODEL.md)
- **Deployment Guide:** [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

## Testing

```bash
# Security tests (185+ tests)
pytest tests/security/ -v

# RBAC tests
pytest tests/security/test_api_auth_rbac.py -v

# LLM safety tests
pytest tests/security/test_llm_safety.py -v

# All unit tests
pytest tests/unit/ -v
```

---

## Status

**Security Implementation:** ✅ Complete  
**Tests:** ✅ 185+ Passing  
**SAST:** ✅ Bandit + Semgrep  
**SBOM:** ✅ Generated on Release  
**CodeQL:** ✅ 0 Vulnerabilities  
**Production Ready:** ✅ Yes  

---

## Support

For security issues, see [SECURITY_POLICY.md](SECURITY_POLICY.md) for responsible disclosure procedures.
