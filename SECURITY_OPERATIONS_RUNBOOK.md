# MLSDM Security Operations Runbook

**Version**: 1.1  
**Last Updated**: December 2025  
**Audience**: DevOps Engineers, Security Engineers, SREs

## Table of Contents

- [Overview](#overview)
- [Security Architecture](#security-architecture)
- [Deployment Checklist](#deployment-checklist)
- [Security Monitoring](#security-monitoring)
- [Incident Response](#incident-response)
- [Key Rotation](#key-rotation)
- [Troubleshooting](#troubleshooting)

---

## Overview

This runbook provides operational procedures for managing MLSDM's security features in production environments. It covers deployment, monitoring, incident response, and maintenance of security components.

### Security Features

MLSDM v1.1 includes the following security features:

1. **Authentication & Authorization**
   - OIDC (OpenID Connect) for SSO integration
   - mTLS (Mutual TLS) for certificate-based authentication
   - RBAC (Role-Based Access Control) for fine-grained permissions
   - Request signing for API integrity verification

2. **Content Security**
   - Policy-as-code engine for request evaluation
   - LLM input/output guardrails
   - LLM safety analysis (toxicity, bias detection)
   - PII scrubbing in logs

3. **Operational Security**
   - Rate limiting
   - Multi-tenant data isolation
   - Security event logging
   - Audit trails

---

## Security Architecture

### Security Middleware Stack

```
Request Flow (Outer → Inner):
┌────────────────────────────────────┐
│ 1. SecurityHeadersMiddleware       │ ← Always enabled
├────────────────────────────────────┤
│ 2. RequestLoggingMiddleware        │ ← If PII scrubbing enabled
├────────────────────────────────────┤
│ 3. MTLSMiddleware                  │ ← If mTLS enabled
├────────────────────────────────────┤
│ 4. OIDCAuthMiddleware              │ ← If OIDC enabled
├────────────────────────────────────┤
│ 5. RBACMiddleware                  │ ← If RBAC enabled
├────────────────────────────────────┤
│ 6. SigningMiddleware               │ ← If signing enabled
├────────────────────────────────────┤
│ 7. RequestIDMiddleware             │ ← Always enabled
├────────────────────────────────────┤
│ 8. TimeoutMiddleware               │ ← Always enabled
├────────────────────────────────────┤
│ 9. PriorityMiddleware              │ ← Always enabled
├────────────────────────────────────┤
│ 10. BulkheadMiddleware             │ ← Always enabled
└────────────────────────────────────┘
```

### Request Processing Pipeline

```
1. Authentication (OIDC/mTLS)
   ↓
2. Authorization (RBAC)
   ↓
3. Policy Evaluation (Policy Engine)
   ↓
4. Input Guardrails
   ↓
5. LLM Safety Analysis (Input)
   ↓
6. LLM Generation
   ↓
7. Output Guardrails
   ↓
8. LLM Safety Analysis (Output)
   ↓
9. Response
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Review and update security configuration in `env.prod.example`
- [ ] Verify OIDC provider configuration and connectivity
- [ ] Generate/obtain mTLS certificates (if using mTLS)
- [ ] Create signing keys for request signature verification
- [ ] Configure secrets manager (AWS Secrets Manager, HashiCorp Vault, etc.)
- [ ] Review and update RBAC role mappings
- [ ] Test security features in staging environment

### Production Deployment

#### Step 1: Configure Security Profile

```bash
# Set production runtime mode
export MLSDM_RUNTIME_MODE=cloud-prod

# This enables all security features by default
# To customize, override specific features
```

#### Step 2: Configure OIDC (if enabled)

```bash
# OIDC configuration
export MLSDM_SECURITY_ENABLE_OIDC=1
export MLSDM_OIDC_DISCOVERY_URL=https://your-idp.example.com/.well-known/openid-configuration
export MLSDM_OIDC_CLIENT_ID=<client-id>
export MLSDM_OIDC_CLIENT_SECRET=<client-secret>
export MLSDM_OIDC_AUDIENCE=mlsdm-api

# Optional: Custom claims for roles
export MLSDM_OIDC_ROLES_CLAIM=roles
```

#### Step 3: Configure mTLS (if enabled)

```bash
# mTLS configuration
export MLSDM_SECURITY_ENABLE_MTLS=1
export MLSDM_MTLS_CA_CERT=/path/to/ca-bundle.crt
export MLSDM_MTLS_REQUIRE_CLIENT_CERT=true
export MLSDM_MTLS_VERIFY_DEPTH=3

# Server-side TLS (uvicorn)
uvicorn mlsdm.api.app:app \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile /path/to/server.key \
  --ssl-certfile /path/to/server.crt \
  --ssl-ca-certs /path/to/ca-bundle.crt \
  --ssl-cert-reqs 2  # CERT_REQUIRED
```

#### Step 4: Configure Request Signing (if enabled)

```bash
# Request signing configuration
export MLSDM_SECURITY_ENABLE_REQUEST_SIGNING=1
export MLSDM_SIGNING_KEY=<your-hmac-signing-key>
export MLSDM_SIGNING_ALGORITHM=HS256
export MLSDM_SIGNING_MAX_AGE=300  # 5 minutes
```

#### Step 5: Configure RBAC (if enabled)

```bash
# RBAC configuration
export MLSDM_SECURITY_ENABLE_RBAC=1

# Default roles: read, write, admin
# Roles are extracted from OIDC token or mTLS certificate
```

#### Step 6: Enable Content Security Features

```bash
# Policy engine
export MLSDM_SECURITY_ENABLE_POLICY_ENGINE=1

# Guardrails
export MLSDM_SECURITY_ENABLE_GUARDRAILS=1

# LLM safety analysis
export MLSDM_SECURITY_ENABLE_LLM_SAFETY=1

# PII scrubbing
export MLSDM_SECURITY_ENABLE_PII_SCRUB_LOGS=1
```

#### Step 7: Enable Multi-Tenancy (if SaaS)

```bash
# Multi-tenant enforcement
export MLSDM_SECURITY_ENABLE_MULTI_TENANT_ENFORCEMENT=1

# Tenant ID will be extracted from:
# - OIDC JWT claims: tenant_id, tenantId, organization_id, org_id
# - mTLS certificate: O (organizationName), OU (organizationalUnitName)
```

#### Step 8: Start Application

```bash
# Using uvicorn directly
uvicorn mlsdm.api.app:app \
  --host 0.0.0.0 \
  --port 8443 \
  --workers 4 \
  --ssl-keyfile /path/to/server.key \
  --ssl-certfile /path/to/server.crt

# Or using Docker
docker run -d \
  --name mlsdm-api \
  -p 8443:8443 \
  -e MLSDM_RUNTIME_MODE=cloud-prod \
  -e MLSDM_SECURITY_ENABLE_OIDC=1 \
  -e MLSDM_OIDC_DISCOVERY_URL=https://idp.example.com/.well-known/openid-configuration \
  -v /path/to/certs:/certs \
  mlsdm:latest
```

### Post-Deployment Validation

- [ ] Verify OIDC authentication is working
  ```bash
  curl -H "Authorization: Bearer <valid-token>" https://api.example.com/health
  ```

- [ ] Verify mTLS is working
  ```bash
  curl --cert client.crt --key client.key --cacert ca.crt https://api.example.com/health
  ```

- [ ] Verify RBAC is enforcing permissions
  ```bash
  # Should fail without admin role
  curl -H "Authorization: Bearer <user-token>" https://api.example.com/admin/stats
  ```

- [ ] Verify policy engine is blocking invalid requests
- [ ] Verify guardrails are active
- [ ] Check security logs for startup events
- [ ] Verify PII scrubbing in logs

---

## Security Monitoring

### Key Metrics to Monitor

1. **Authentication Failures**
   - Metric: `mlsdm_auth_failures_total`
   - Alert: > 100/minute
   - Action: Investigate potential brute force attack

2. **Policy Violations**
   - Metric: `mlsdm_policy_violations_total`
   - Alert: Sudden spike
   - Action: Review policy logs

3. **Rate Limit Exceeded**
   - Metric: `mlsdm_rate_limit_exceeded_total`
   - Alert: > 1000/minute
   - Action: Investigate potential DDoS

4. **Guardrail Blocks**
   - Metric: `mlsdm_guardrail_blocks_total`
   - Alert: Unusual patterns
   - Action: Review blocked content

5. **Safety Analysis Blocks**
   - Metric: `mlsdm_safety_blocks_total`
   - Alert: High rate
   - Action: Investigate input sources

### Log Queries

#### View Authentication Failures
```bash
# Assuming structured JSON logs
jq 'select(.event_type == "auth_failure")' < /var/log/mlsdm/security.log
```

#### View Policy Violations
```bash
jq 'select(.event_type == "policy_violation")' < /var/log/mlsdm/security.log
```

#### View Blocked Requests
```bash
jq 'select(.guardrails_blocked == true or .safety_blocked == true)' < /var/log/mlsdm/api.log
```

---

## Incident Response

### Authentication Failure Spike

**Symptoms**: High rate of authentication failures

**Possible Causes**:
- Expired tokens
- Misconfigured OIDC provider
- Brute force attack

**Response**:
1. Check OIDC provider status
2. Review authentication logs
3. If brute force attack:
   - Enable IP-based rate limiting
   - Block suspicious IPs at firewall/WAF
   - Notify security team

### Policy Violation Spike

**Symptoms**: High rate of policy violations

**Possible Causes**:
- New attack vector
- Misconfigured policy
- Legitimate traffic pattern change

**Response**:
1. Review policy violation logs
2. Identify common patterns
3. If attack: Update policies
4. If legitimate: Adjust policies

### Guardrail Block Spike

**Symptoms**: High rate of guardrail blocks

**Possible Causes**:
- Malicious input attempts
- Bug in client application
- Overly restrictive guardrails

**Response**:
1. Review blocked content (scrubbed)
2. Identify source (client_id, user_id)
3. If malicious: Block source
4. If legitimate: Adjust guardrails

---

## Key Rotation

### OIDC Client Secret Rotation

```bash
# 1. Generate new client secret in IdP
NEW_SECRET=<new-secret>

# 2. Update application config
kubectl set env deployment/mlsdm-api MLSDM_OIDC_CLIENT_SECRET=$NEW_SECRET

# 3. Restart application (rolling restart)
kubectl rollout restart deployment/mlsdm-api

# 4. Verify authentication still works
curl -H "Authorization: Bearer <token>" https://api.example.com/health

# 5. Revoke old secret in IdP
```

### Request Signing Key Rotation

```bash
# 1. Generate new signing key
NEW_KEY=$(openssl rand -base64 32)

# 2. Update key in secrets manager
aws secretsmanager update-secret \
  --secret-id mlsdm/signing-key \
  --secret-string "$NEW_KEY"

# 3. Update application (will pick up new key on restart)
kubectl rollout restart deployment/mlsdm-api

# 4. Update clients with new key
# (coordinate with API consumers)

# 5. Monitor for signature verification failures
```

### mTLS Certificate Rotation

```bash
# 1. Generate new certificates
# (using your PKI process)

# 2. Update certificates on server
kubectl create secret tls mlsdm-tls \
  --cert=new-server.crt \
  --key=new-server.key \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. Rolling restart
kubectl rollout restart deployment/mlsdm-api

# 4. Distribute new client certificates
# (coordinate with API consumers)

# 5. Monitor for mTLS failures
```

---

## Troubleshooting

### OIDC Authentication Not Working

**Problem**: Users cannot authenticate

**Debug Steps**:
1. Check OIDC configuration
   ```bash
   curl $MLSDM_OIDC_DISCOVERY_URL
   ```

2. Check logs for OIDC errors
   ```bash
   grep "OIDC\|JWT" /var/log/mlsdm/api.log
   ```

3. Verify token structure
   ```bash
   # Decode JWT (do NOT log full token)
   echo "$TOKEN" | cut -d. -f2 | base64 -d | jq
   ```

4. Common issues:
   - Expired token (check `exp` claim)
   - Wrong audience (check `aud` claim)
   - Clock skew (sync server time)
   - Missing required claims

### mTLS Certificate Validation Failures

**Problem**: Clients rejected with certificate errors

**Debug Steps**:
1. Verify CA certificate is correct
   ```bash
   openssl verify -CAfile ca.crt client.crt
   ```

2. Check certificate chain
   ```bash
   openssl x509 -in client.crt -text -noout
   ```

3. Verify certificate not expired
4. Check certificate subject matches expected pattern
5. Verify client is sending certificate

### Policy Engine Blocking Legitimate Requests

**Problem**: Valid requests are denied by policy engine

**Debug Steps**:
1. Check policy logs for denial reason
2. Review PolicyContext for the request
3. Verify user roles/permissions
4. Check policy rules
5. Temporarily disable policy engine to confirm
   ```bash
   export MLSDM_SECURITY_ENABLE_POLICY_ENGINE=0
   ```

### Guardrails Blocking Valid Content

**Problem**: Legitimate prompts/responses are blocked

**Debug Steps**:
1. Review guardrail logs
2. Check safety scores
3. Adjust guardrail thresholds if needed
4. Temporarily disable guardrails to confirm
   ```bash
   export MLSDM_SECURITY_ENABLE_GUARDRAILS=0
   ```

---

## Appendix

### Security Configuration Reference

See `env.prod.example` for complete configuration reference.

### Related Documentation

- [SECURITY_POLICY.md](SECURITY_POLICY.md) - Comprehensive security policy
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Deployment procedures
- [THREAT_MODEL.md](THREAT_MODEL.md) - Threat model and mitigations
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation

### Support

For security issues, contact: security@example.com (configure for your organization)

For operational support, contact: ops@example.com (configure for your organization)
