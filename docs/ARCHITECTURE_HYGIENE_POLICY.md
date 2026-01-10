# Architecture Hygiene Policy (CIO Standard)

This policy governs **structure**, **boundaries**, and **change discipline**. It does
**not** alter system objectives or runtime behavior; it enforces professional-grade
architectural integrity.

## Objectives

1. Prevent cross-layer coupling and dependency drift.
2. Preserve testable, auditable module boundaries.
3. Ensure changes are traceable to contracts and specs.
4. Maintain a single source of truth for structure.

## Scope

Applies to any change that:
- Adds/removes/renames modules under `src/mlsdm/`
- Introduces new top-level directories
- Modifies dependency directionality
- Changes public interfaces (API/SDK/CLI)

## Non-negotiable rules

1. **Single responsibility**: each module has one primary responsibility.
2. **Manifest authority**: `architecture_manifest.py` defines allowed dependencies.
3. **No cross-layer imports**: violations are treated as defects.
4. **Contract alignment**: public interfaces must be documented and tested.
5. **Doc-code parity**: documentation must match code reality at merge time.

## Required updates for structural changes

When structure changes, update all items below:
- `src/mlsdm/config/architecture_manifest.py`
- `tests/contracts/test_architecture_manifest.py`
- `docs/ARCHITECTURE_SPEC.md`
- `docs/REPO_ARCHITECTURE_MAP.md`
- `docs/CONTRACT_BOUNDARY_INDEX.md`

## Validation gate

Before merge:
- `pytest tests/contracts/test_architecture_manifest.py`

## Review checklist (minimum)

- [ ] Module responsibility is explicit and documented.
- [ ] Dependency changes match `architecture_manifest.py`.
- [ ] Contract tests updated and passing.
- [ ] Repo map and boundary index reflect the new structure.

