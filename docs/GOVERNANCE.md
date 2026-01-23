# Governance

**Document Version:** 1.0.0
**Last Updated:** January 2025
**Status:** Active

## Overview

This document is the **single entry point** for repository governance. It defines what is governed, how governance is enforced, and where to find authoritative rules.

---

## Governance Principles

1. **Single Source of Truth (SSOT)**: Each concern has exactly one authoritative source
2. **Docs↔Validators Isomorphism**: Every enforced rule is documented; no undocumented enforcement
3. **Evidence-Based Claims**: All claims must be backed by verifiable evidence
4. **Consistent Terminology**: Standard terms are used consistently across all documents

---

## What Is Governed

### Governed Artifacts

| Artifact | Governance Type | Validator |
|----------|-----------------|-----------|
| Bibliography | SSOT closure | `scripts/validate_bibliography.py` |
| Documentation claims | Code parity | `scripts/verify_docs_claims_against_code.py` |
| API contracts | Schema validation | `scripts/verify_docs_contracts.py` |
| Security invariants | Path/config validation | `scripts/verify_security_skip_invariants.py` |
| CI workflows | Policy checks | `.github/workflows/*.yml` |

### SSOT Documents

| Document | Authoritative For |
|----------|-------------------|
| [bibliography/REFERENCES.bib](bibliography/REFERENCES.bib) | BibTeX citations |
| [bibliography/REFERENCES_APA7.md](bibliography/REFERENCES_APA7.md) | Human-readable references |
| [bibliography/metadata/identifiers.json](bibliography/metadata/identifiers.json) | DOI/URL metadata |
| [CLAIMS_TRACEABILITY.md](CLAIMS_TRACEABILITY.md) | Metric-to-test mapping |
| [CLAIM_EVIDENCE_LEDGER.md](CLAIM_EVIDENCE_LEDGER.md) | Evidence anchors |
| [status/READINESS.md](status/READINESS.md) | Readiness status |

---

## Enforcement

### Validation Scripts

| Script | Purpose | Exit Code |
|--------|---------|-----------|
| `validate_bibliography.py` | Validates BibTeX↔APA↔metadata consistency | 0=pass, 1=fail |
| `verify_docs_claims_against_code.py` | Validates doc claims match code | 0=pass, 1=fail |
| `verify_docs_contracts.py` | Validates API contract docs | 0=pass, 1=fail |
| `verify_security_skip_invariants.py` | Validates security path configs | 0=pass, 1=fail |

### Running Governance Checks

```bash
# Run all SSOT validation
make ssot

# Individual validators
python scripts/validate_bibliography.py
python scripts/verify_docs_claims_against_code.py

# Full verification suite
make verify-docs
make verify-security-skip
```

### CI Enforcement

Governance checks are enforced in CI workflows:

| Workflow | Governance Checks |
|----------|-------------------|
| `ci-smoke.yml` | Security invariants, smoke tests |
| `prod-gate.yml` | Full lint, type, tests, security scan |
| `citation-integrity.yml` | Bibliography validation |

---

## Terminology

Standard terms used throughout the repository:

| Term | Definition |
|------|------------|
| **SSOT** | Single Source of Truth — authoritative artifact for a concern |
| **Tier-A** | Core subsystem with full test coverage and contracts |
| **Tier-S** | Safety-critical subsystem with additional invariants |
| **Claim ID** | Unique identifier for a verifiable claim (e.g., CLM-001) |
| **Normative** | Required/mandatory statement (not optional) |
| **Governed docs** | Documents subject to validation and enforcement |
| **Validation tests** | Tests verifying documented claims |
| **Smoke tests** | Fast feedback tests (< 5 min) |
| **Evidence artifact** | Verifiable output proving a claim |

---

## Claims Governance

### Claim Lifecycle

1. **Creation**: Claim documented with ID, metric, and evidence anchor
2. **Verification**: Test or benchmark validates claim
3. **Traceability**: Claim linked to test in [CLAIMS_TRACEABILITY.md](CLAIMS_TRACEABILITY.md)
4. **Evidence**: Results stored in `artifacts/evidence/`

### Claim Format

```markdown
| Claim ID | Metric | Value | Evidence |
|----------|--------|-------|----------|
| CLM-001 | Toxic rejection rate | 93.3% | test_moral_filter_effectiveness.py |
```

---

## Bibliography Governance

### SSOT Structure

```
docs/bibliography/
├── REFERENCES.bib           # BibTeX (machine-readable)
├── REFERENCES_APA7.md       # APA7 (human-readable)
├── VERIFICATION.md          # Verification status
└── metadata/
    └── identifiers.json     # DOI/URL metadata
```

### Rules

1. Every BibTeX entry must have an APA7 equivalent
2. DOI/URL metadata must be verified
3. Verification status tracked in `VERIFICATION.md`
4. Validation script enforces consistency

---

## Documentation Governance

### Governed Documents

All documents in `docs/` are subject to:
- Link validity checks
- Terminology consistency
- Version synchronization

### Non-Governed Documents

See [INVENTORY.md](INVENTORY.md) for the authoritative list of non-governed paths. Key categories include:
- `docs/archive/` — Historical documents (read-only)
- `examples/` — User examples (not normative)
- `artifacts/` — Generated artifacts (ephemeral)

---

## Audit Trail

### Finding Tracking

Structural issues are tracked in [AUDIT_FINDINGS.md](AUDIT_FINDINGS.md):
- Unique finding ID (FND-XXXX)
- Root cause analysis
- Resolution status

### Review Cycle

- **Per-PR**: Governance checks in CI
- **Per-release**: Full audit review
- **Quarterly**: Comprehensive governance review

---

## Related Documents

- [INDEX.md](INDEX.md) — Navigation hub
- [INVENTORY.md](INVENTORY.md) — Governed paths list
- [CLAIMS_TRACEABILITY.md](CLAIMS_TRACEABILITY.md) — Claims verification
- [DOCUMENTATION_FORMALIZATION_PROTOCOL.md](DOCUMENTATION_FORMALIZATION_PROTOCOL.md) — Documentation standards

---

**This document is the single governance entry point. All governance rules should be traceable from here.**
