# Technical Debt Ledger

**Last Updated:** December 2025
**Related:** [ENGINEERING_DEFICIENCIES_REGISTER.md](ENGINEERING_DEFICIENCIES_REGISTER.md)

---

## Summary

| Status | Count |
|--------|-------|
| Resolved | 1 |
| Open | 37 (mypy type errors) |
| Total | 38 |

See [ENGINEERING_DEFICIENCIES_REGISTER.md](ENGINEERING_DEFICIENCIES_REGISTER.md) for comprehensive analysis.

---

## DL-001 (RESOLVED)

- Priority: P3
- Gate: test
- Symptom: RuntimeWarning about overflow encountered in dot during TestMemoryContentSafety::test_extreme_magnitude_vectors.
- Evidence: artifacts/baseline/test.log (numpy/linalg/_linalg.py:2792 RuntimeWarning: overflow encountered in dot, triggered by tests/safety/test_memory_leakage.py::TestMemoryContentSafety::test_extreme_magnitude_vectors).
- Likely root cause: Test inputs use extremely large vectors causing numpy.linalg dot product to overflow.
- Fix applied: Implemented safe_norm() function in src/mlsdm/utils/math_constants.py that uses scaled norm computation to prevent overflow. Updated phase_entangled_lattice_memory.py and multi_level_memory.py to use safe_norm() instead of np.linalg.norm().
- Proof command: source .venv/bin/activate && make test
- Risk: None - safe_norm() produces identical results for normal vectors and handles extreme magnitudes safely.
- Date: 2025-12-15
- Fixed: 2025-12-17
- Owner: @copilot
- Status: resolved
- Next action: None - issue is resolved.

---

## DL-002 (OPEN)

- Priority: P4 (Low)
- Gate: type-check
- Symptom: 37 mypy errors when running `mypy src/mlsdm`
- Evidence: mypy output shows errors including:
  - 9x "Class cannot subclass 'BaseHTTPMiddleware' (has type 'Any')"
  - 15x "Untyped decorator makes function untyped"
  - 6x "Returning Any from function"
  - 2x "Library stubs not installed"
- Likely root cause: FastAPI/Starlette typing limitations and missing type stubs
- Risk: Low - code functions correctly, typing is for developer experience
- Date: 2025-12-19
- Owner: @team
- Status: open
- Next action: Install types-PyYAML and types-requests, add type: ignore comments with documentation

---

## DL-003 (OPEN)

- Priority: P3 (Medium)
- Gate: coverage
- Symptom: Test coverage at 70.85%, below target of 75%
- Evidence: COVERAGE_REPORT_2025.md shows 70.85% overall coverage
- Likely root cause: Insufficient tests for api/, security/, observability/ modules
- Risk: Medium - potential for undetected bugs
- Date: 2025-12-19
- Owner: @team
- Status: open
- Next action: Add tests to increase coverage to 75%
