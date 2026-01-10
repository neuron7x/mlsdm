# Ownership & Responsibility Matrix (Operational)

This matrix defines subsystem accountability and contract boundaries. It is a
process artifact; it does **not** change runtime behavior.

## Principles

- Ownership is required for every subsystem.
- Ownership implies responsibility for contracts, tests, and docs.
- Cross-subsystem changes require explicit coordination.

## Ownership map

| Subsystem | Responsibility | Primary contracts/specs |
| --- | --- | --- |
| `api/` | HTTP surface, request validation, response contracts. | `docs/API_REFERENCE.md`, `docs/API_CONTRACT.md` |
| `core/` | Cognitive orchestration and pipelines. | `docs/ARCHITECTURE_SPEC.md` |
| `engine/` | Runtime assembly and wiring. | `docs/NEURO_COG_ENGINE_SPEC.md` |
| `memory/` | Multi-level memory + PELM. | `docs/NEURO_FOUNDATIONS.md` |
| `rhythm/` | Cognitive rhythm/phase control. | `docs/NEURO_FOUNDATIONS.md` |
| `speech/` | Aphasia detection and repair. | `docs/APHASIA_SPEC.md` |
| `security/` | Governance, safety guardrails. | `docs/SECURITY_POLICY.md`, `SAFETY_POLICY.yaml` |
| `observability/` | Metrics/logging/tracing. | `docs/OBSERVABILITY_SPEC.md` |
| `router/` | LLM routing and failover. | `docs/LLM_ADAPTERS_AND_ROUTER.md` |
| `adapters/` | Provider integrations. | `docs/LLM_ADAPTERS_AND_FACTORY.md` |
| `sdk/` | Client SDK. | `docs/SDK_USAGE.md` |
| `utils/` | Shared primitives/config helpers. | `docs/DEVELOPER_GUIDE.md` |

## Contract boundaries

Subsystem dependencies must follow:
- `src/mlsdm/config/architecture_manifest.py`
- `tests/contracts/test_architecture_manifest.py`

## Change coordination

For cross-subsystem changes:
- Notify all affected subsystem owners.
- Update contracts/specs together in the same change set.

