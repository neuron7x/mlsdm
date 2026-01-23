# Repository Inventory

**Document Version:** 1.0.0
**Last Updated:** January 2025
**Status:** Active

## Overview

This document is the **authoritative inventory** of repository paths, categorizing them as governed (subject to validation) or non-governed (informational/archived).

---

## Directory Structure

```
mlsdm/
├── src/                    # Implementation (Tier-A/Tier-S)
├── tests/                  # Test suite (governed)
├── docs/                   # Documentation (governed)
├── scripts/                # Enforcement scripts (governed)
├── .github/workflows/      # CI definitions (governed)
├── config/                 # Configuration (governed)
├── benchmarks/             # Performance benchmarks
├── artifacts/              # Generated artifacts
├── examples/               # User examples (non-governed)
├── reports/                # Generated reports
└── [root files]            # Project configuration
```

---

## Governed Paths

### Tier-A: Core Implementation

These paths contain core logic with full test coverage and contracts.

| Path | Description | Validator |
|------|-------------|-----------|
| `src/mlsdm/core/` | Core cognitive components | Unit tests, property tests |
| `src/mlsdm/api/` | API layer | Contract tests |
| `src/mlsdm/engine/` | Engine orchestration | Integration tests |
| `src/mlsdm/security/` | Security components | Security tests |

### Tier-S: Safety-Critical

These paths contain safety-critical code with additional invariants.

| Path | Description | Additional Governance |
|------|-------------|----------------------|
| `src/mlsdm/core/moral_filter.py` | Moral governance | Property tests, formal invariants |
| `src/mlsdm/speech/` | Speech governance | Detection accuracy tests |
| `src/mlsdm/security/policy_engine.py` | Policy enforcement | Security invariant tests |

### Documentation

| Path | Description | Validator |
|------|-------------|-----------|
| `docs/*.md` | Primary documentation | Link validation, terminology checks |
| `docs/bibliography/` | SSOT bibliography | `validate_bibliography.py` |
| `docs/status/` | Readiness tracking | Evidence validation |
| `docs/adr/` | Architecture decisions | Format validation |

### Configuration

| Path | Description | Validator |
|------|-------------|-----------|
| `pyproject.toml` | Project configuration | CI builds |
| `pytest.ini` | Test configuration | Test collection |
| `config/default_config.yaml` | Runtime config | Schema validation |
| `.github/workflows/*.yml` | CI workflows | Policy checks |

### Scripts

| Path | Description | Validator |
|------|-------------|-----------|
| `scripts/validate_*.py` | Validation scripts | Self-tests |
| `scripts/verify_*.py` | Verification scripts | Exit codes |
| `scripts/ci/` | CI helper scripts | CI execution |
| `scripts/evidence/` | Evidence capture | Snapshot verification |

### Tests

| Path | Description | Marker |
|------|-------------|--------|
| `tests/unit/` | Unit tests | `unit` |
| `tests/integration/` | Integration tests | `integration` |
| `tests/property/` | Property-based tests | `property` |
| `tests/security/` | Security tests | `security` |
| `tests/validation/` | Validation tests | `validation` |
| `tests/e2e/` | End-to-end tests | `e2e` |
| `tests/eval/` | Evaluation tests | — |
| `tests/contracts/` | Contract tests | — |

---

## Non-Governed Paths

### Archives

| Path | Description | Status |
|------|-------------|--------|
| `docs/archive/` | Historical documents | Read-only, not validated |
| `docs/archive/checklists/` | Legacy checklists | Deprecated |
| `docs/archive/prompts/` | Historical prompts | Reference only |
| `docs/archive/reports/` | Historical reports | Superseded |

### User-Facing Examples

| Path | Description | Status |
|------|-------------|--------|
| `examples/` | Code examples | Informational, not normative |
| `evals/` | Evaluation scripts | User-facing |

### Generated Artifacts

| Path | Description | Status |
|------|-------------|--------|
| `artifacts/` | Build/test artifacts | Generated, ephemeral |
| `reports/` | Generated reports | Output only |
| `coverage.xml` | Coverage report | Generated |

### External Dependencies

| Path | Description | Status |
|------|-------------|--------|
| `sdk/` | SDK code | Separate module |
| `deploy/` | Deployment configs | Environment-specific |
| `docker/` | Docker configs | Environment-specific |

### Load Tests (Excluded from Standard Runs)

| Path | Description | Status |
|------|-------------|--------|
| `tests/load/` | Load/stress tests | Excluded via `--ignore=tests/load` |

---

## Governance Matrix

| Path Pattern | Governed | CI Enforced | SSOT |
|--------------|----------|-------------|------|
| `src/**/*.py` | ✅ | ✅ | — |
| `tests/**/*.py` (except load) | ✅ | ✅ | — |
| `docs/*.md` | ✅ | ✅ | — |
| `docs/bibliography/**` | ✅ | ✅ | ✅ |
| `docs/archive/**` | ❌ | ❌ | — |
| `scripts/**/*.py` | ✅ | ✅ | — |
| `.github/workflows/**` | ✅ | ✅ | — |
| `config/**` | ✅ | ✅ | — |
| `examples/**` | ❌ | ❌ | — |
| `artifacts/**` | ❌ | ❌ | — |

---

## Test Markers

Tests are organized by markers defined in `pytest.ini`:

| Marker | Description | CI Job |
|--------|-------------|--------|
| `slow` | Long-running tests | Excluded from smoke |
| `smoke` | Fast feedback tests | `ci-smoke.yml` |
| `integration` | Integration tests | `prod-gate.yml` |
| `unit` | Unit tests | All CI jobs |
| `property` | Property-based tests | `property-tests.yml` |
| `security` | Security tests | `sast-scan.yml` |
| `validation` | Validation tests | Validation suite |
| `benchmark` | Performance tests | `perf-resilience.yml` |
| `e2e` | End-to-end tests | `prod-gate.yml` |
| `load` | Load tests | Manual/scheduled |
| `chaos` | Chaos tests | `chaos-tests.yml` |
| `comprehensive` | Comprehensive tests | Separate job |

---

## Related Documents

- [INDEX.md](INDEX.md) — Navigation hub
- [GOVERNANCE.md](GOVERNANCE.md) — Governance rules
- [TESTING_STRATEGY.md](TESTING_STRATEGY.md) — Testing approach
- [CI_GUIDE.md](CI_GUIDE.md) — CI documentation

---

**This document is the authoritative inventory of governed paths.**
