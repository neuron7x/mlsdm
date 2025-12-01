# MLSDM Governance Layer

**Document Version:** 1.0.0  
**Last Updated:** December 2025  
**Status:** Production

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Operating Modes](#operating-modes)
- [Policy Configuration](#policy-configuration)
- [Enforcer Usage](#enforcer-usage)
- [Pipeline Integration](#pipeline-integration)
- [Metrics and Observability](#metrics-and-observability)
- [Testing and Evaluation](#testing-and-evaluation)
- [Configuration Reference](#configuration-reference)

---

## Overview

The MLSDM Governance Layer provides content governance and safety enforcement for the cognitive memory system. It implements a policy-driven approach to filtering, modifying, or escalating content based on configurable rules and operating modes.

### Key Features

| Feature | Description |
|---------|-------------|
| **Policy-Driven** | Declarative YAML-based policy configuration |
| **Three Modes** | Normal, Cautious, and Emergency operating modes |
| **Rule Engine** | Priority-based rule evaluation with multiple action types |
| **Actions** | Allow, Block, Modify, Escalate |
| **Metrics** | Prometheus-compatible governance metrics |
| **Audit Logging** | Structured logging of all governance decisions |

### Design Principles

1. **Fail-Safe**: Unknown inputs default to conservative behavior
2. **Configurable**: All thresholds and rules defined in policy file
3. **Observable**: All decisions logged and metricated
4. **Composable**: Integrates with existing pipeline filters

---

## Architecture

### Component Structure

```
src/mlsdm/governance/
├── __init__.py       # Public API exports
├── policy.yaml       # Declarative policy configuration
├── enforcer.py       # Core evaluation and decision logic
└── metrics.py        # Governance metrics collection
```

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LLM Pipeline                                  │
│                                                                      │
│  ┌──────────┐    ┌─────────────────┐    ┌──────────┐    ┌─────────┐ │
│  │  Input   │───▶│  Pre-Governance │───▶│   LLM    │───▶│  Post   │ │
│  │ Payload  │    │   (evaluate)    │    │  Call    │    │ Filter  │ │
│  └──────────┘    └────────┬────────┘    └──────────┘    └─────────┘ │
│                           │                                          │
│                           ▼                                          │
│                  ┌─────────────────┐                                │
│                  │  Governance     │                                │
│                  │  Decision       │                                │
│                  │                 │                                │
│                  │  • action       │                                │
│                  │  • reason       │                                │
│                  │  • rule_id      │                                │
│                  │  • mode         │                                │
│                  └────────┬────────┘                                │
│                           │                                          │
│                           ▼                                          │
│                  ┌─────────────────┐                                │
│                  │ apply_decision  │                                │
│                  │                 │                                │
│                  │  allow ──▶ pass │                                │
│                  │  block ──▶ None │                                │
│                  │  modify ──▶ mod │                                │
│                  │  escalate ──▶ ∅ │                                │
│                  └─────────────────┘                                │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Operating Modes

The governance layer supports three operating modes with progressively stricter thresholds:

### Normal Mode

Standard operating mode for typical usage.

| Parameter | Value | Description |
|-----------|-------|-------------|
| `moral_threshold` | 0.50 | Moral filter threshold |
| `toxicity_threshold` | 0.70 | Toxicity block threshold |
| `block_on_uncertainty` | false | Don't block uncertain content |
| `escalation_enabled` | false | Escalation disabled |
| `log_level` | info | Standard logging |

### Cautious Mode

Elevated security for sensitive contexts (medical, financial, legal).

| Parameter | Value | Description |
|-----------|-------|-------------|
| `moral_threshold` | 0.65 | Higher moral threshold |
| `toxicity_threshold` | 0.50 | Lower toxicity tolerance |
| `block_on_uncertainty` | true | Block high-uncertainty content |
| `escalation_enabled` | true | Enable human escalation |
| `log_level` | warning | Elevated logging |

### Emergency Mode

Lockdown mode for critical security situations.

| Parameter | Value | Description |
|-----------|-------|-------------|
| `moral_threshold` | 0.80 | Strictest moral threshold |
| `toxicity_threshold` | 0.30 | Very low toxicity tolerance |
| `block_on_uncertainty` | true | Block any uncertain content |
| `escalation_enabled` | true | All risks escalated |
| `log_level` | error | Error-level logging |

### Mode Selection

Modes can be selected explicitly or automatically based on context:

```python
from mlsdm.governance import select_mode

# Automatic selection based on context
mode = select_mode({
    "request_context": ["medical"],  # → cautious
    "consecutive_rejections": 150,   # → emergency
})
```

**Emergency Triggers:**
- `consecutive_rejections >= 100`
- `rejection_rate >= 0.8` (5 min window)
- `memory_usage_percent >= 95`

**Cautious Contexts:**
- medical
- financial
- legal
- minors

---

## Policy Configuration

### File Location

```
src/mlsdm/governance/policy.yaml
```

### Rule Structure

```yaml
rules:
  - id: "R001"                    # Unique identifier
    description: "Block toxicity" # Human-readable description
    priority: 100                 # Higher = evaluated first
    enabled: true                 # Can be disabled
    trigger:
      condition: "toxicity_score >= mode.toxicity_threshold"
      signals:
        - "toxicity_score"
    action: "block"               # allow | block | modify | escalate
    log_level: "error"
    response_message: "Request blocked due to safety concerns."
    metadata:
      category: "toxicity"
```

### Signal Definitions

```yaml
signals:
  moral_value:
    type: "float"
    range: [0.0, 1.0]
    default: 0.5
    description: "Moral score from moral filter"

  toxicity_score:
    type: "float"
    range: [0.0, 1.0]
    default: 0.0
    description: "Toxicity score from content analysis"

  pii_detected:
    type: "boolean"
    default: false
    description: "Whether PII was detected"
```

---

## Enforcer Usage

### Basic Usage

```python
from mlsdm.governance import evaluate, apply_decision

# Prepare context with signal values
context = {
    "mode": "normal",
    "moral_value": 0.75,
    "toxicity_score": 0.2,
    "pii_detected": False,
}

# Evaluate the request
decision = evaluate(
    input_payload={"prompt": "user question"},
    output_payload={"response": "LLM response"},
    context=context,
)

# Check decision
if decision.action == "allow":
    # Proceed with output
    final_output = output_payload
elif decision.action == "block":
    # Return error/rejection
    final_output = None
elif decision.action == "modify":
    # Apply modifications
    final_output = apply_decision(decision, output_payload)
elif decision.action == "escalate":
    # Flag for human review
    final_output = None
    # queue_for_review(decision)
```

### GovernanceDecision Fields

| Field | Type | Description |
|-------|------|-------------|
| `action` | str | "allow", "block", "modify", "escalate" |
| `reason` | str | Human-readable explanation |
| `rule_id` | str | ID of matched rule (e.g., "R001") |
| `mode` | str | Current operating mode |
| `metadata` | dict | Additional context (modification type, etc.) |

---

## Pipeline Integration

### With LLMPipeline

```python
from mlsdm.core.llm_pipeline import LLMPipeline, PipelineConfig
from mlsdm.governance import evaluate, apply_decision, select_mode

class GovernancePreFilter:
    """Pre-filter integrating governance evaluation."""

    def evaluate(self, prompt: str, context: dict) -> FilterResult:
        # Select mode based on context
        mode = select_mode(context)

        # Evaluate governance
        decision = evaluate(
            input_payload={"prompt": prompt},
            output_payload=None,
            context={**context, "mode": mode},
        )

        if decision.action == "block":
            return FilterResult(
                decision=FilterDecision.BLOCK,
                reason=decision.reason,
                metadata={"rule_id": decision.rule_id},
            )

        return FilterResult(decision=FilterDecision.ALLOW)
```

### With LLMWrapper

```python
from mlsdm.core.llm_wrapper import LLMWrapper
from mlsdm.governance import evaluate, apply_decision, record_governance_decision

# After LLM generates response
response = wrapper.generate(prompt=prompt, moral_value=moral_value)

if response["accepted"]:
    # Apply governance post-check
    decision = evaluate(
        input_payload={"prompt": prompt},
        output_payload={"response": response["response"]},
        context={"moral_value": moral_value, "mode": "normal"},
    )

    record_governance_decision(decision)

    if decision.action != "allow":
        response = apply_decision(decision, response)
```

---

## Metrics and Observability

### Governance Metrics

```python
from mlsdm.governance import (
    get_governance_summary,
    get_governance_metrics,
    record_governance_decision,
    set_governance_mode,
)

# Record decisions
record_governance_decision(decision)

# Set mode for gauge
set_governance_mode("cautious")

# Get summary
summary = get_governance_summary()
# {
#     "total_decisions": 1000,
#     "block_rate": 0.05,
#     "modify_rate": 0.02,
#     "escalate_rate": 0.001,
#     "allow_rate": 0.929,
#     "current_mode": "normal",
#     "mode_transitions": 3,
#     "top_rules": [("R007", 929), ("R002", 30), ...]
# }
```

### Available Metrics

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `decisions_by_action` | Counter | action | Decisions per action type |
| `decisions_by_mode` | Counter | mode | Decisions per mode |
| `decisions_by_rule` | Counter | rule_id | Decisions per rule |
| `blocked_total` | Counter | - | Total blocked requests |
| `modified_total` | Counter | - | Total modified responses |
| `escalated_total` | Counter | - | Total escalated requests |
| `current_mode` | Gauge | - | Current mode (0/1/2) |
| `mode_transitions` | Counter | - | Total mode transitions |

### Log Format

```json
{
  "event": "governance_decision",
  "timestamp": "2025-12-01T10:00:00Z",
  "rule_id": "R002",
  "action": "block",
  "mode": "normal",
  "reason": "Block content failing moral evaluation"
}
```

**Note:** Logs do not include sensitive content (prompts/responses) to protect privacy.

---

## Testing and Evaluation

### Running Tests

```bash
# Run governance tests
pytest tests/governance/test_enforcer.py -v

# Run with coverage
pytest tests/governance/ --cov=src/mlsdm/governance --cov-report=term-missing
```

### Running Evaluation

```bash
# Run all evaluations
python evals/governance_eval.py --mode all --verbose

# Run specific evaluations
python evals/governance_eval.py --mode scenarios      # Test scenarios
python evals/governance_eval.py --mode comparison     # Mode comparison
python evals/governance_eval.py --mode selection      # Mode selection
```

### Test Categories

| Category | Description | File |
|----------|-------------|------|
| Policy Loading | Policy file loads correctly | `test_enforcer.py::TestPolicyLoading` |
| Basic Evaluation | Allow/block decisions | `test_enforcer.py::TestBasicEvaluation` |
| Mode Variations | Mode-specific behavior | `test_enforcer.py::TestModeVariations` |
| Specific Rules | Individual rule testing | `test_enforcer.py::TestSpecificRules` |
| Apply Decision | Decision application | `test_enforcer.py::TestApplyDecision` |
| Mode Selection | Automatic mode selection | `test_enforcer.py::TestModeSelection` |
| Metrics | Metrics recording | `test_enforcer.py::TestGovernanceMetrics` |
| Integration | End-to-end flows | `test_enforcer.py::TestIntegrationScenarios` |

---

## Configuration Reference

### Policy File Schema

```yaml
metadata:
  version: string      # Policy version
  name: string         # Policy name
  description: string  # Description

modes:
  normal:
    moral_threshold: float      # 0.0-1.0
    toxicity_threshold: float   # 0.0-1.0
    block_on_uncertainty: bool
    escalation_enabled: bool
    pii_check_enabled: bool
    max_retries: int
    response_timeout_seconds: int
    log_level: string          # debug|info|warning|error

  cautious: ...
  emergency: ...

rules:
  - id: string           # Unique rule ID
    description: string  # Human-readable description
    priority: int        # Higher = evaluated first
    enabled: bool        # Enable/disable rule
    trigger:
      condition: string  # Evaluation expression
      signals: list      # Required signal names
    action: string       # allow|block|modify|escalate
    log_level: string
    response_message: string  # For block/escalate
    modification: string      # For modify action
    disclaimer_text: string   # For add_disclaimer
    metadata: dict

signals:
  signal_name:
    type: string         # float|boolean|string
    range: [min, max]    # For numeric types
    default: any         # Default value
    description: string

mode_selection:
  emergency_triggers:
    consecutive_rejections: int
    rejection_rate_5min: float
    memory_usage_percent: int
  cautious_contexts:
    - string
  default_mode: string
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MLSDM_GOVERNANCE_MODE` | Override default mode | `normal` |
| `MLSDM_GOVERNANCE_STRICT` | Enable strict validation | `false` |

---

## References

- [SAFETY_POLICY.yaml](../SAFETY_POLICY.yaml) - Extended safety categories
- [MORAL_FILTER_SPEC.md](../MORAL_FILTER_SPEC.md) - Moral filter details
- [THREAT_MODEL.md](../THREAT_MODEL.md) - Security threat analysis
- [docs/ALIGNMENT_AND_SAFETY_FOUNDATIONS.md](ALIGNMENT_AND_SAFETY_FOUNDATIONS.md) - Safety foundations

---

**Document Status:** Production  
**Review Cycle:** Per major version  
**Last Reviewed:** December 2025
