# Repository Architecture Map (Canonical)

This map is the authoritative navigation guide for MLSDM. It describes **what lives
where**, **why it exists**, and **what contracts govern it**. It does not change
system goals or runtime behavior; it prevents structural drift and ambiguity.

## Purpose

- Provide a stable, canonical map for maintainers and reviewers.
- Reduce onboarding time and audit friction.
- Ensure every subsystem is backed by a specification and contract tests.

## Top-level layout (source-of-truth)

| Path | Responsibility | Notes |
| --- | --- | --- |
| `src/` | Production code for MLSDM. | All runtime logic lives here. |
| `docs/` | Specifications, protocols, rationale, and audits. | Governance for change. |
| `tests/` | Contracts, unit, integration, e2e, and property tests. | Enforces invariants. |
| `scripts/` | Validation and CI tooling. | No business logic. |
| `config/` | Runtime configuration defaults/templates. | Environment-specific only. |
| `deploy/` | Deployment manifests and service runtime. | Non-code infra. |
| `policies/`, `policy/` | Governance/safety policies. | Human + machine readable. |
| `reports/` | Evidence, audits, metrics output. | Immutable outputs. |
| `benchmarks/` | Benchmark harnesses and baselines. | Evaluation only. |
| `assets/` | Diagrams and static artifacts. | Documentation support. |

## Core module map (source: `src/mlsdm/`)

| Module | Primary responsibility | Key contracts/specs |
| --- | --- | --- |
| `api/` | HTTP API surface, request/response contracts. | `docs/API_REFERENCE.md`, `docs/API_CONTRACT.md` |
| `core/` | Cognitive orchestration and pipelines. | `docs/ARCHITECTURE_SPEC.md` |
| `engine/` | Engine composition and runtime wiring. | `docs/NEURO_COG_ENGINE_SPEC.md` |
| `memory/` | Multi-level memory + PELM primitives. | `docs/NEURO_FOUNDATIONS.md` |
| `rhythm/` | Cognitive rhythm / phase control. | `docs/NEURO_FOUNDATIONS.md` |
| `speech/` | Aphasia detection/repair governance. | `docs/APHASIA_SPEC.md` |
| `security/` | Guardrails, governance, policy enforcement. | `docs/SECURITY_POLICY.md`, `SAFETY_POLICY.yaml` |
| `observability/` | Metrics/logging/tracing. | `docs/OBSERVABILITY_SPEC.md` |
| `router/` | LLM routing & failover. | `docs/LLM_ADAPTERS_AND_ROUTER.md` |
| `adapters/` | Provider integrations. | `docs/LLM_ADAPTERS_AND_FACTORY.md` |
| `sdk/` | Client SDK surface. | `docs/SDK_USAGE.md` |
| `utils/` | Shared primitives and config helpers. | `docs/DEVELOPER_GUIDE.md` |

## Contract enforcement (non-negotiable)

Architecture boundaries are enforced by:
- `src/mlsdm/config/architecture_manifest.py`
- `tests/contracts/test_architecture_manifest.py`

## Change requirements

Any structural change must update:
- This file (`docs/REPO_ARCHITECTURE_MAP.md`)
- `docs/ARCHITECTURE_SPEC.md`
- `src/mlsdm/config/architecture_manifest.py`
- Contract tests (`tests/contracts/test_architecture_manifest.py`)

