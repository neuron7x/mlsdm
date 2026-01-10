# Architecture Change Control (CIO Standard)

This protocol governs structural changes without changing system goals or logic.

## When this applies

Use this protocol if you:
- Add/remove a top-level directory
- Add/rename/split a subsystem under `src/mlsdm/`
- Change cross-layer dependencies
- Introduce or modify a public API surface

## Required artifacts (must be updated in the same change set)

1. `src/mlsdm/config/architecture_manifest.py`
2. `tests/contracts/test_architecture_manifest.py`
3. `docs/ARCHITECTURE_SPEC.md`
4. `docs/REPO_ARCHITECTURE_MAP.md`
5. `docs/CONTRACT_BOUNDARY_INDEX.md`

## Change checklist

- [ ] Dependencies comply with the manifest (no cross-layer violations)
- [ ] Public interfaces are documented
- [ ] Contract tests updated and passing
- [ ] Documentation synced across all architecture docs

## Evidence requirements

Attach evidence to the PR:
- Test output for `tests/contracts/test_architecture_manifest.py`
- Updated specs with references to modified modules

