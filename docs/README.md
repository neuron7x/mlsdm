# MLSDM Documentation Index

**Project**: MLSDM Governed Cognitive Memory  
**Version**: 1.2.0  
**Last Updated**: 2025-12-28

Welcome to the MLSDM documentation. This index provides navigation to all project documentation organized by audience and purpose.

---

## Quick Start

New to MLSDM? Start here:

1. **[Getting Started Guide](GETTING_STARTED.md)** - 15-minute onboarding with installation and first run
2. **[Architecture Overview](ARCHITECTURE.md)** - System components and data flow
3. **[Configuration Guide](CONFIGURATION_GUIDE.md)** - How to configure the system

---

## Core Documentation

### For Developers

- **[Getting Started](GETTING_STARTED.md)** - Installation, setup, and verification
- **[Architecture](ARCHITECTURE.md)** - MLE 2024 system design and components
- **[Contributing](../CONTRIBUTING.md)** - How to contribute code and documentation
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Comprehensive development workflow
- **[Testing Guide](TESTING_GUIDE.md)** - Test strategy and writing tests
- **[Evaluation](EVALUATION.md)** - Quality measures and acceptance criteria

### For Operators

- **[Runbook](RUNBOOK.md)** - Operations, troubleshooting, and incident response
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Deployment configurations and strategies
- **[Observability Guide](OBSERVABILITY_GUIDE.md)** - Metrics, logging, and tracing
- **[Configuration Guide](CONFIGURATION_GUIDE.md)** - Configuration options and examples

### For API Users

- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[API HTTP](API_HTTP.md)** - HTTP API endpoints and contracts
- **[SDK Usage](SDK_USAGE.md)** - Using the Python SDK client
- **[Integration Guide](INTEGRATION_GUIDE.md)** - Integrating with external systems

---

## Specifications & Design

### Architecture & Design

- **[Architecture Specification](ARCHITECTURE_SPEC.md)** - Detailed technical architecture
- **[Architecture Configuration](ARCHITECTURE_CONFIG.md)** - Configuration architecture
- **[State System](STATE_SYSTEM.md)** - State management and transitions

### Component Specifications

- **[Neuro Cognitive Engine](NEURO_COG_ENGINE_SPEC.md)** - Core engine specification
- **[LLM Pipeline](LLM_PIPELINE.md)** - LLM routing and pipeline
- **[Moral Filter](MORAL_FILTER_SPEC.md)** - Moral governance specification
- **[Observability Spec](OBSERVABILITY_SPEC.md)** - Observability system design

---

## Evidence & Metrics

- **[Metrics Source of Truth](METRICS_SOURCE.md)** - Test coverage and quality metrics from evidence snapshots
- **[Readiness Status](status/READINESS.md)** - System readiness tracking and change log
- **[Claims Traceability](CLAIMS_TRACEABILITY.md)** - Evidence for project claims

---

## Safety & Security

- **[Security Policy](SECURITY_POLICY.md)** - Security policies and reporting
- **[Security Implementation](SECURITY_IMPLEMENTATION.md)** - Security features implementation
- **[Security Guardrails](SECURITY_GUARDRAILS.md)** - Runtime security guardrails
- **[Threat Model](THREAT_MODEL.md)** - Security threat analysis
- **[Safety Foundations](ALIGNMENT_AND_SAFETY_FOUNDATIONS.md)** - AI safety principles

---

## Testing & Quality

- **[Evaluation](EVALUATION.md)** - How we measure quality and correctness
- **[Testing Strategy](TESTING_STRATEGY.md)** - Comprehensive testing approach
- **[Test Strategy](TEST_STRATEGY.md)** - Test suite organization
- **[Component Test Matrix](COMPONENT_TEST_MATRIX.md)** - Component coverage matrix

---

## CI/CD & Workflows

- **[CI Guide](CI_GUIDE.md)** - Continuous integration workflows
- **[CI Security Gating](CI_SECURITY_GATING.md)** - Security gate implementation
- **[Tools and Scripts](TOOLS_AND_SCRIPTS.md)** - Development tools reference

---

## Research & Experimental

- **[Scientific Rationale](SCIENTIFIC_RATIONALE.md)** - Neuroscientific foundations
- **[Neuro Foundations](NEURO_FOUNDATIONS.md)** - Neurobiological principles
- **[Aphasia Specification](APHASIA_SPEC.md)** - Language pathology detection
- **[Benchmark Baseline](BENCHMARK_BASELINE.md)** - Performance benchmarks

---

## Registers & Tracking

- **[Risk Register](RISK_REGISTER.md)** - Known risks and mitigations
- **[Audit Register](AUDIT_REGISTER.md)** - Audit findings and actions
- **[Technical Debt Register](TECHNICAL_DEBT_REGISTER.md)** - Technical debt tracking
- **[Engineering Deficiencies](ENGINEERING_DEFICIENCIES_REGISTER.md)** - Known gaps

---

## Archive

- **[ADR (Architecture Decision Records)](adr/)** - Design decisions and rationale
- **[Archive](archive/)** - Historical documentation and reports

---

## Documentation Standards

This documentation follows MLE 2024 production hygiene standards:

- **Truth-first**: All claims grounded in repository files or evidence snapshots
- **Reproducible**: All commands are executable and verified
- **Evidence-based**: Metrics sourced from `artifacts/evidence/` snapshots
- **No guessing**: Unknown items marked as "NOT VERIFIED" with verification steps

### Documentation Maintenance

- Keep documentation synchronized with code changes
- Update [READINESS.md](status/READINESS.md) when changing src/, tests/, config/, deploy/, or workflows
- Reference evidence snapshots (not CI URLs) in [METRICS_SOURCE.md](METRICS_SOURCE.md)
- Run `make readiness-preview` before updating READINESS.md

---

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/neuron7x/mlsdm/issues)
- **Discussions**: Use GitHub Discussions for questions
- **Contributing**: See [CONTRIBUTING.md](../CONTRIBUTING.md)

---

**Navigation**: [↑ Back to Repository Root](../)
