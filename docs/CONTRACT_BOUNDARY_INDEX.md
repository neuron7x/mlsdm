# Contract Boundary Index

This index defines subsystem boundaries and enforcement points. It is the
cross-reference for architectural contracts.

## Core contracts

| Subsystem | Contract references | Enforcement |
| --- | --- | --- |
| Architecture manifest | `src/mlsdm/config/architecture_manifest.py` | `tests/contracts/test_architecture_manifest.py` |
| API surface | `docs/API_CONTRACT.md`, `docs/API_REFERENCE.md` | `tests/api/` |
| Speech governance | `docs/APHASIA_SPEC.md` | `tests/contracts/test_speech_contracts.py` |
| Observability | `docs/OBSERVABILITY_SPEC.md` | `tests/observability/` |
| Security policy | `docs/SECURITY_POLICY.md`, `SAFETY_POLICY.yaml` | `tests/security/` |

## Boundary rules

1. The manifest is the dependency source of truth.
2. Contract tests are required for public interface changes.
3. Documentation must be consistent with code-level contracts at merge time.

## Review gates

- Architecture manifest is updated (if structure changes).
- Contract tests pass for modified boundaries.
- Docs reflect reality (no stale paths or modules).

