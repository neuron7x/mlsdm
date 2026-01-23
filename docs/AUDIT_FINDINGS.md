# Audit Findings Ledger

**Document Version:** 1.0.0
**Last Updated:** January 2025
**Status:** Active

## Overview

This document records structural findings identified during repository architecture unification. Each finding has a unique identifier, symptom description, root cause, affected files, recommended fix, and acceptance criteria.

---

## Status Legend

| Status | Description |
|--------|-------------|
| ✅ **Resolved** | Finding addressed and verified |
| 🔄 **In Progress** | Fix implementation underway |
| ⚠️ **Open** | Identified but not yet addressed |

---

## Active Findings

### FND-0001: Missing Validation Marker in pytest.ini

**Status:** ✅ Resolved

**Symptom:** `pytest -m validation` collects no tests, despite `tests/validation/` containing test files.

**Root Cause:** The `validation` marker is not defined in `pytest.ini`, so validation tests cannot be filtered via markers.

**Anchors:**
- `pytest.ini:4-15` — marker definitions

**Fix:** Add `validation` marker to `pytest.ini` marker list.

**Acceptance Criteria:**
- `pytest -m validation --collect-only` collects tests from `tests/validation/`
- `pytest -m "not validation"` excludes validation tests

---

### FND-0002: Missing Single Navigation Hub Document

**Status:** ✅ Resolved

**Symptom:** `docs/index.md` serves as documentation index but is not the canonical navigation hub with explicit governance/architecture/SSOT links.

**Root Cause:** The index document evolved organically without a structured navigation contract.

**Anchors:**
- `docs/index.md` — existing index file

**Fix:** Create `docs/INDEX.md` as the canonical navigation hub with explicit links to governance, architecture, SSOT, and reproducibility docs.

**Acceptance Criteria:**
- `docs/INDEX.md` exists and links to all canonical entry points
- Root README links to INDEX.md as navigation hub

---

### FND-0003: Missing Governance Entry Point

**Status:** ✅ Resolved

**Symptom:** Governance rules are scattered across multiple documents without a single entry point.

**Root Cause:** No dedicated governance document consolidating SSOT rules, validators, claims, and bibliography policies.

**Anchors:**
- `docs/DOCUMENTATION_FORMALIZATION_PROTOCOL.md` — partial governance
- `docs/status/READINESS.md` — partial governance
- `scripts/validate_bibliography.py` — bibliography enforcement
- `scripts/verify_docs_claims_against_code.py` — claims enforcement

**Fix:** Create `docs/GOVERNANCE.md` as a single-page governance entry linking to all enforcement mechanisms.

**Acceptance Criteria:**
- `docs/GOVERNANCE.md` exists
- Document links to SSOT rules, validators, claims ledger, bibliography

---

### FND-0004: Missing Governed Paths Inventory

**Status:** ✅ Resolved

**Symptom:** No authoritative list of which paths are governed (subject to validation) vs. non-governed.

**Root Cause:** Path governance evolved implicitly without documentation.

**Anchors:**
- Repository root structure
- CI workflow definitions

**Fix:** Create `docs/INVENTORY.md` with explicit governed and non-governed path lists.

**Acceptance Criteria:**
- `docs/INVENTORY.md` exists
- Document clearly delineates governed vs. non-governed paths

---

### FND-0005: Load Tests Import Error

**Status:** ⚠️ Open (Non-blocking)

**Symptom:** `tests/load/standalone_server_load_test.py` and `tests/load/test_async_utils.py` fail to import due to missing `async_utils` module.

**Root Cause:** Local module import without proper path configuration. The `async_utils.py` file exists in `tests/load/` but is imported as a top-level module.

**Anchors:**
- `tests/load/standalone_server_load_test.py:44`
- `tests/load/test_async_utils.py:10`

**Fix:** Use relative imports or add `tests/load/__init__.py` and update imports. Note: Load tests are excluded from standard test runs via `--ignore=tests/load`.

**Acceptance Criteria:**
- Import errors resolved when load tests are run directly
- No impact on standard test runs (already excluded)

---

### FND-0006: Root README Not a System Launchpad

**Status:** ✅ Resolved

**Symptom:** Root README provides good overview but lacks explicit links to governance, SSOT gates, and validation commands.

**Root Cause:** README evolved as user-facing documentation without explicit architecture navigation.

**Anchors:**
- `README.md`

**Fix:** Update README to include repository map, SSOT gate commands, and explicit links to governance and architecture docs.

**Acceptance Criteria:**
- README includes repository structure map
- README includes SSOT validation commands
- README links to INDEX.md as navigation hub

---

## Resolved Findings Archive

Findings that have been resolved are moved here with resolution notes.

---

## Audit Process

### Finding Format

```markdown
### FND-XXXX: [Title]

**Status:** [Status Badge]

**Symptom:** [Observable behavior or issue]

**Root Cause:** [Why this occurs]

**Anchors:**
- `path/file:line` — description

**Fix:** [Recommended resolution]

**Acceptance Criteria:**
- [Verifiable condition]
```

### Review Cycle

- Findings are created during architecture audits
- Findings are resolved during unification work
- Resolved findings are archived with resolution notes

---

**Document Owner:** Repository Architecture
**Review Cycle:** Per audit iteration
