# Repository Navigation Hub

**Document Version:** 1.0.0
**Last Updated:** January 2025
**Status:** Active

## Overview

This is the **canonical navigation hub** for the MLSDM repository. Use this document to find any resource by purpose.

---

## Quick Navigation

| Purpose | Document | Description |
|---------|----------|-------------|
| **Start Here** | [README.md](../README.md) | Project overview and quick start |
| **Architecture** | [ARCHITECTURE_SPEC.md](ARCHITECTURE_SPEC.md) | System architecture and design |
| **Governance** | [GOVERNANCE.md](GOVERNANCE.md) | Validation rules and enforcement |
| **Inventory** | [INVENTORY.md](INVENTORY.md) | Governed and non-governed paths |
| **API Reference** | [API_REFERENCE.md](API_REFERENCE.md) | Complete API documentation |
| **Reproducibility** | [status/READINESS.md](status/READINESS.md) | Evidence-based readiness status |

---

## Documentation Categories

### 🎯 Getting Started

| Document | Audience | Purpose |
|----------|----------|---------|
| [README.md](../README.md) | Everyone | Project overview, installation, quick start |
| [USAGE_GUIDE.md](USAGE_GUIDE.md) | Developers | Integration patterns and examples |
| [GETTING_STARTED.md](GETTING_STARTED.md) | New users | First-time setup guide |
| [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md) | DevOps | Configuration reference |

### 🏗️ Architecture & Design

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE_SPEC.md](ARCHITECTURE_SPEC.md) | System architecture |
| [NEURO_FOUNDATIONS.md](NEURO_FOUNDATIONS.md) | Scientific foundations |
| [SCIENTIFIC_RATIONALE.md](SCIENTIFIC_RATIONALE.md) | Research rationale |
| [adr/](adr/) | Architecture Decision Records |

### 📋 Governance & Compliance

| Document | Purpose |
|----------|---------|
| [GOVERNANCE.md](GOVERNANCE.md) | Single governance entry point |
| [INVENTORY.md](INVENTORY.md) | Governed paths list |
| [CLAIMS_TRACEABILITY.md](CLAIMS_TRACEABILITY.md) | Claims-to-evidence mapping |
| [CLAIM_EVIDENCE_LEDGER.md](CLAIM_EVIDENCE_LEDGER.md) | Evidence ledger |
| [AUDIT_FINDINGS.md](AUDIT_FINDINGS.md) | Structural audit findings |
| [DOCUMENTATION_FORMALIZATION_PROTOCOL.md](DOCUMENTATION_FORMALIZATION_PROTOCOL.md) | Documentation standards |

### 🔬 Bibliography & References

| Document | Purpose |
|----------|---------|
| [bibliography/README.md](bibliography/README.md) | Bibliography overview |
| [bibliography/REFERENCES.bib](bibliography/REFERENCES.bib) | BibTeX references |
| [bibliography/REFERENCES_APA7.md](bibliography/REFERENCES_APA7.md) | APA7 formatted references |
| [bibliography/VERIFICATION.md](bibliography/VERIFICATION.md) | Reference verification status |

### 🛡️ Security & Safety

| Document | Purpose |
|----------|---------|
| [SECURITY_POLICY.md](SECURITY_POLICY.md) | Security guidelines |
| [THREAT_MODEL.md](THREAT_MODEL.md) | Threat analysis |
| [RISK_REGISTER.md](RISK_REGISTER.md) | AI safety risk register |
| [MORAL_FILTER_SPEC.md](MORAL_FILTER_SPEC.md) | Moral governance spec |

### 🧪 Testing & Validation

| Document | Purpose |
|----------|---------|
| [TESTING_STRATEGY.md](TESTING_STRATEGY.md) | Testing approach |
| [TEST_STRATEGY.md](TEST_STRATEGY.md) | Test strategy details |
| [CLAIMS_TRACEABILITY.md](CLAIMS_TRACEABILITY.md) | Claims verification |

### 🚀 Deployment & Operations

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Deployment patterns |
| [RUNBOOK.md](RUNBOOK.md) | Operational runbook |
| [SLO_SPEC.md](SLO_SPEC.md) | Service level objectives |
| [OBSERVABILITY_GUIDE.md](OBSERVABILITY_GUIDE.md) | Monitoring and observability |

### 📊 Status & Tracking

| Document | Purpose |
|----------|---------|
| [status/READINESS.md](status/READINESS.md) | Evidence-based readiness |
| [TECHNICAL_DEBT_REGISTER.md](TECHNICAL_DEBT_REGISTER.md) | Technical debt tracking |
| [ENGINEERING_DEFICIENCIES_REGISTER.md](ENGINEERING_DEFICIENCIES_REGISTER.md) | Deficiency registry |

---

## Scripts & Tools

### Validation Scripts

| Script | Purpose | Invocation |
|--------|---------|------------|
| `scripts/validate_bibliography.py` | Validate bibliography SSOT | `python scripts/validate_bibliography.py` |
| `scripts/verify_docs_claims_against_code.py` | Validate claims against code | `python scripts/verify_docs_claims_against_code.py` |
| `scripts/verify_docs_contracts.py` | Verify documentation contracts | `make verify-docs` |
| `scripts/verify_security_skip_invariants.py` | Verify security invariants | `make verify-security-skip` |

### Make Targets

| Target | Purpose |
|--------|---------|
| `make ssot` | Run SSOT validation (bibliography + claims) |
| `make test-smoke` | Run smoke tests (fast feedback) |
| `make test-validation` | Run validation tests |
| `make ci-local` | Run full local CI (ssot + smoke) |
| `make lint` | Run linter |
| `make type` | Run type checker |
| `make test` | Run all tests |

---

## Archive

Historical and deprecated documents are located in:

- [archive/checklists/](archive/checklists/) — Legacy checklists
- [archive/prompts/](archive/prompts/) — Historical prompts
- [archive/reports/](archive/reports/) — Historical reports
- [archive/bibliography/](archive/bibliography/) — Archived bibliography items

---

## External Links

- **GitHub Repository**: https://github.com/neuron7x/mlsdm
- **Issue Tracker**: https://github.com/neuron7x/mlsdm/issues
- **CI Status**: https://github.com/neuron7x/mlsdm/actions

---

**This document is the canonical navigation hub. All important resources should be discoverable from here.**
