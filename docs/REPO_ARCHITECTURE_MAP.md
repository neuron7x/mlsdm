# Repository Architecture Map (Canonical)

This document is the **single, canonical** navigation map for MLSDM. It defines
where responsibilities live, what contracts govern them, and what must be updated
when structure changes. It does **not** alter system goals or runtime behavior.

## Objectives

- Provide a stable repository map for maintainers and audits.
- Anchor architectural boundaries to contracts and tests.
- Prevent structural drift via explicit change requirements.

## Top-level layout (source-of-truth)

| Path | Responsibility | Governance signal |
| --- | --- | --- |
| `src/` | Production code for MLSDM. | Runtime behavior lives here. |
| `docs/` | Specifications, protocols, audits. | Architecture + governance. |
| `tests/` | Contract/unit/integration/e2e/property tests. | Invariant enforcement. |
| `scripts/` | Validation and CI tooling. | No business logic. |
| `config/` | Runtime defaults/templates. | Environment-specific only. |
| `deploy/` | Deployment manifests. | Infrastructure boundary. |
| `policies/`, `policy/` | Governance & safety policy. | Human + machine readable. |
| `reports/` | Evidence and audit output. | Immutable artifacts. |
| `benchmarks/` | Benchmark harnesses/baselines. | Evaluation only. |
| `assets/` | Static diagrams/artifacts. | Documentation support. |

## Core module map (source: `src/mlsdm/`)

| Module | Primary responsibility | Canonical spec/contracts |
| --- | --- | --- |
| `api/` | HTTP API surface and contracts. | `docs/API_REFERENCE.md`, `docs/API_CONTRACT.md` |
| `core/` | Cognitive orchestration and pipelines. | `docs/ARCHITECTURE_SPEC.md` |
| `engine/` | Runtime assembly and wiring. | `docs/NEURO_COG_ENGINE_SPEC.md` |
| `memory/` | Multi-level memory + PELM. | `docs/NEURO_FOUNDATIONS.md` |
| `rhythm/` | Cognitive rhythm/phase control. | `docs/NEURO_FOUNDATIONS.md` |
| `speech/` | Aphasia detection/repair governance. | `docs/APHASIA_SPEC.md` |
| `security/` | Guardrails and policy enforcement. | `docs/SECURITY_POLICY.md`, `SAFETY_POLICY.yaml` |
| `observability/` | Metrics/logging/tracing. | `docs/OBSERVABILITY_SPEC.md` |
| `router/` | LLM routing and failover. | `docs/LLM_ADAPTERS_AND_ROUTER.md` |
| `adapters/` | Provider integrations. | `docs/LLM_ADAPTERS_AND_FACTORY.md` |
| `sdk/` | Client SDK surface. | `docs/SDK_USAGE.md` |
| `utils/` | Shared primitives/config helpers. | `docs/DEVELOPER_GUIDE.md` |

## Contract enforcement (non-negotiable)

Architecture boundaries are enforced by:
- `src/mlsdm/config/architecture_manifest.py`
- `tests/contracts/test_architecture_manifest.py`

## Structural change requirements (must-update set)

Any structural change must update **all** items below:
- `docs/REPO_ARCHITECTURE_MAP.md`
- `docs/ARCHITECTURE_SPEC.md`
- `docs/CONTRACT_BOUNDARY_INDEX.md`
- `src/mlsdm/config/architecture_manifest.py`
- `tests/contracts/test_architecture_manifest.py`

