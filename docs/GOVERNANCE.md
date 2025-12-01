# Governance Module Documentation

**Document Version:** 1.0.0  
**Project Version:** 1.2.0  
**Last Updated:** December 2025  
**Status:** Production

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Operational Modes](#operational-modes)
- [Policy Configuration](#policy-configuration)
- [Enforcer API](#enforcer-api)
- [Pipeline Integration](#pipeline-integration)
- [Metrics & Logging](#metrics--logging)
- [Testing](#testing)

---

## Overview

The MLSDM Governance module provides policy-based content governance for the cognitive engine. It evaluates input prompts and output responses against configurable rules to determine whether content should be allowed, blocked, modified, or escalated for human review.

### Key Features

1. **Mode-Based Operation**: Three operational modes (normal, cautious, emergency) with different strictness levels
2. **Rule-Based Evaluation**: Configurable rules for content governance
3. **PII Detection**: Automatic detection of personal identifiable information
4. **Toxicity Enforcement**: Block or modify toxic content
5. **Moral Threshold Enforcement**: Integration with MoralFilterV2
6. **Audit Logging**: Structured logging for compliance and debugging
7. **Metrics Collection**: Prometheus-compatible metrics export

### Design Principles

- **Fail-Safe Defaults**: Unknown or invalid inputs default to rejection
- **Defense in Depth**: Multiple layers of validation
- **Observable**: All decisions are logged and metrified
- **Configurable**: Policy changes without code deployment
- **Testable**: Comprehensive test coverage

---

## Architecture

### Module Structure

```
src/mlsdm/governance/
├── __init__.py       # Public API exports
├── policy.yaml       # Policy configuration
├── enforcer.py       # Core enforcement logic
└── metrics.py        # Metrics collection
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     NeuroCognitiveEngine                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Governance Enforcer                     │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │  │
│  │  │   Policy    │  │    Mode     │  │     Rule        │   │  │
│  │  │   Loader    │→ │  Selector   │→ │   Evaluator     │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘   │  │
│  │         │                                    │            │  │
│  │         ▼                                    ▼            │  │
│  │  ┌─────────────┐              ┌─────────────────────┐    │  │
│  │  │   Signal    │              │    Governance       │    │  │
│  │  │  Extractor  │              │     Decision        │    │  │
│  │  └─────────────┘              └─────────────────────┘    │  │
│  │                                          │                │  │
│  └──────────────────────────────────────────┼────────────────┘  │
│                                             ▼                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Apply Decision                         │  │
│  │    allow → pass through  |  block → return None          │  │
│  │    modify → add disclaimer  |  escalate → mark for review│  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input Evaluation**: Before LLM generation, evaluate input prompt
2. **Output Evaluation**: After LLM generation, evaluate response
3. **Decision Application**: Apply governance decision to output

---

## Operational Modes

The governance system operates in one of three modes, each with different strictness levels:

### Normal Mode (Default)

- **Moral Threshold**: 0.50
- **Checks**: PII, Toxicity
- **Response Modification**: Allowed
- **Log Level**: INFO

Use for general-purpose requests with standard safety requirements.

### Cautious Mode

- **Moral Threshold**: 0.70
- **Checks**: PII, Toxicity, Market Risk
- **Response Modification**: Allowed
- **Log Level**: WARNING

Triggered by:
- Medium risk level (≥0.5)
- Sensitive domain context
- Anonymous users

### Emergency Mode

- **Moral Threshold**: 0.90
- **Checks**: All enabled, strict thresholds
- **Response Modification**: Disabled (block uncertain content)
- **Log Level**: ERROR

Triggered by:
- High risk level (≥0.8)
- Critical safety concerns

### Mode Selection Logic

```python
# Mode is selected based on context signals:
if context.mode is not None:
    return context.mode  # Explicit override
elif context.risk_level >= 0.8:
    return "emergency"
elif context.risk_level >= 0.5 or context.sensitive_domain:
    return "cautious"
else:
    return "normal"
```

---

## Policy Configuration

### policy.yaml Structure

```yaml
modes:
  normal:
    moral_threshold: 0.50
    pii_check: true
    toxicity_check: true
    log_level: "info"
  cautious:
    moral_threshold: 0.70
    ...
  emergency:
    moral_threshold: 0.90
    ...

rules:
  - id: "R001"
    description: "Block PII content"
    priority: 100
    trigger:
      type: "pattern"
      signals: ["pii_detected"]
    action: "block"
    log: "error"

  - id: "R002"
    description: "Block high toxicity"
    priority: 90
    trigger:
      type: "threshold"
      signal: "toxicity_score"
      operator: "gte"
      value: 0.8
    action: "block"
    ...
```

### Rule Actions

| Action | Description | Result |
|--------|-------------|--------|
| `allow` | Pass content through | Output unchanged |
| `block` | Reject content | Returns None |
| `modify` | Alter content | Adds disclaimer/warning |
| `escalate` | Mark for review | Output with escalation metadata |

### Trigger Types

1. **pattern**: Match presence of signals (e.g., PII detected)
2. **threshold**: Compare signal value against threshold
3. **compound**: Multiple conditions (AND logic)
4. **default**: Always matches (fallback rule)

### Signal Configuration

```yaml
signals:
  toxicity_score:
    source: "output"
    path: "metadata.toxicity"
    default: 0.0

  pii_detected:
    source: "computed"
    extractor: "pii_pattern_matcher"
```

---

## Enforcer API

### evaluate()

Evaluate governance rules against payloads.

```python
from mlsdm.governance import evaluate, GovernanceDecision

decision: GovernanceDecision = evaluate(
    input_payload={"prompt": "Hello", "moral_value": 0.5},
    output_payload={"response": "Hi!", "metadata": {"toxicity": 0.1}},
    context={"risk_level": 0.3}
)

print(f"Action: {decision.action}")
print(f"Rule: {decision.rule_id}")
print(f"Mode: {decision.mode}")
print(f"Reason: {decision.reason}")
```

### apply_decision()

Apply governance decision to output.

```python
from mlsdm.governance import apply_decision

result = apply_decision(decision, output_payload)

if result is None:
    # Content was blocked
    return {"error": decision.reason}
else:
    # Content allowed (possibly modified)
    return result
```

### GovernanceDecision

```python
@dataclass
class GovernanceDecision:
    action: str        # "allow" | "block" | "modify" | "escalate"
    reason: str        # Human-readable explanation
    rule_id: str | None  # Rule that triggered decision
    mode: str          # Operational mode used
    metadata: dict     # Additional data (signals, escalation info)
```

### GovernanceContext

```python
@dataclass
class GovernanceContext:
    mode: str | None           # Override mode
    risk_level: float          # 0.0 - 1.0
    sensitive_domain: bool     # Sensitive context flag
    user_type: str             # "authenticated" | "anonymous"
    correlation_id: str | None # Request tracing ID
    additional: dict           # Custom signals
```

---

## Pipeline Integration

### Integration Point

The enforcer is integrated in `NeuroCognitiveEngine._generate_internal()`:

```python
# BEFORE LLM generation: Validate input
input_payload = {"prompt": prompt, "moral_value": moral_value}
decision = evaluate(input_payload, None, context)
if decision.action == "block":
    return self._build_error_response("governance_block", decision.reason, ...)

# LLM generation happens here...

# AFTER LLM generation: Validate output
output_payload = {"response": response_text, "metadata": {...}}
decision = evaluate(input_payload, output_payload, context)
output_payload = apply_decision(decision, output_payload)
if output_payload is None:
    return self._build_error_response("governance_block", decision.reason, ...)
```

### Context Building

```python
context = GovernanceContext(
    mode=None,  # Auto-select based on signals
    risk_level=self._estimate_risk_level(prompt),
    sensitive_domain=self._is_sensitive_domain(user_intent),
    user_type=user_type,
    correlation_id=request_id,
)
```

---

## Metrics & Logging

### Metrics

```python
from mlsdm.governance import get_metrics

metrics = get_metrics()
summary = metrics.get_summary()

# Summary structure:
{
    "total_decisions": 1000,
    "allowed_total": 900,
    "blocked_total": 50,
    "modified_total": 30,
    "escalated_total": 20,
    "block_rate": 0.05,
    "per_mode": {
        "normal": {"total": 800, "blocked": 20, ...},
        "cautious": {"total": 150, "blocked": 25, ...},
        "emergency": {"total": 50, "blocked": 5, ...}
    },
    "per_rule": {
        "R001": 30,
        "R002": 20,
        ...
    }
}
```

### Prometheus Integration

```python
from mlsdm.governance import register_prometheus_metrics

prometheus_metrics = register_prometheus_metrics()
# Registers:
# - mlsdm_governance_decisions_total{action, mode, rule_id}
# - mlsdm_governance_blocked_total{mode, rule_id}
# - mlsdm_governance_modified_total{mode}
# - mlsdm_governance_escalated_total{mode, priority}
# - mlsdm_governance_mode
```

### Structured Logging

```python
from mlsdm.governance import log_governance_event

log_governance_event(
    action="block",
    rule_id="R001",
    mode="normal",
    reason="PII detected in prompt",
    correlation_id="req-123",
    metadata={"log_level": "error"}
)
```

Log output (sanitized, no PII):
```json
{
  "event_type": "governance_decision",
  "action": "block",
  "rule_id": "R001",
  "mode": "normal",
  "reason": "PII detected in prompt",
  "correlation_id": "req-123"
}
```

---

## Testing

### Running Tests

```bash
# Run all governance tests
pytest tests/governance/ -v

# Run specific test class
pytest tests/governance/test_enforcer.py::TestBlockRules -v

# Run with coverage
pytest tests/governance/ --cov=src/mlsdm/governance --cov-report=html
```

### Test Categories

1. **Policy Loading**: PolicyLoader singleton, reload functionality
2. **Mode Selection**: Default mode, explicit override, risk-based selection
3. **Rule Evaluation**: Allow, block, modify, escalate rules
4. **PII Detection**: Email, phone, SSN, credit card patterns
5. **Decision Application**: Payload modification, blocking
6. **Metrics**: Counter increments, per-mode/per-rule tracking
7. **Integration**: Full pipeline tests

### Adding New Rules

1. Add rule to `policy.yaml`
2. Add corresponding test in `test_enforcer.py`
3. Run tests to verify behavior

---

## References

- [SAFETY_POLICY.yaml](../SAFETY_POLICY.yaml) - Content safety categories
- [MORAL_FILTER_SPEC.md](../MORAL_FILTER_SPEC.md) - Moral filter documentation
- [THREAT_MODEL.md](../THREAT_MODEL.md) - Security threat analysis
- [SLO_SPEC.md](../SLO_SPEC.md) - Service level objectives

---

**Document Status:** Production  
**Review Cycle:** Per major version  
**Last Reviewed:** December 2025  
**Next Review:** v2.0.0 release
