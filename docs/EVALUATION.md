# Evaluation: How We Measure Correctness

**Document Version**: 1.0.0  
**Last Updated**: 2025-12-28  
**Status**: Production

This document describes MLSDM's quality measurement approach, test strategy, and acceptance criteria for pull requests and releases.

---

## What "Quality" Means in This Project

Quality in MLSDM is measured across multiple dimensions:

1. **Functional Correctness**: Code behaves as specified (unit/integration tests)
2. **System Integration**: Components work together correctly (E2E tests)
3. **Property Invariants**: System maintains mathematical/logical properties (property-based tests)
4. **Performance**: Meets latency and throughput requirements (benchmarks, perf tests)
5. **Security**: No vulnerabilities or unsafe behaviors (security tests, SAST)
6. **Observability**: Instrumentation works correctly (observability tests)
7. **Resilience**: Graceful failure handling (chaos tests, resilience tests)

---

## Test Suite Organization

Tests are organized under `tests/` by purpose:

```
tests/
├── unit/              # Fast, isolated unit tests
├── integration/       # Component integration tests
├── e2e/               # End-to-end system tests
├── property/          # Property-based tests (Hypothesis)
├── perf/              # Performance/SLO tests
├── observability/     # Metrics/logging/tracing tests
├── security/          # Security invariants and guardrails
├── resilience/        # Fault tolerance and recovery
├── validation/        # Effectiveness validation (moral filter, rhythm)
├── chaos/             # Chaos engineering tests
└── load/              # Load testing (excluded by default)
```

### Test Markers

Tests are marked with pytest markers for selective execution:

- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.integration`: Integration tests (moderate speed)
- `@pytest.mark.property`: Property-based tests (comprehensive)
- `@pytest.mark.slow`: Slow-running tests (skip in fast mode)
- `@pytest.mark.security`: Security-related tests

---

## Minimum Acceptance Suite on PR

**Every PR must pass the following before merge**:

### 1. Readiness Check

```bash
python scripts/readiness_check.py
```

**Checks**:
- `docs/status/READINESS.md` exists
- Last updated date is within 14 days
- If code/tests/config/workflows changed, READINESS.md must be updated

### 2. Unit Tests (Fast)

```bash
make test-fast
# or: pytest tests/unit tests/state -m "not slow and not comprehensive" -q --tb=short
```

**Expected**: All tests pass in < 30 seconds

### 3. Coverage Gate

```bash
make coverage-gate
# or: ./coverage_gate.sh
```

**Threshold**: 75% line coverage (enforced in CI)
**Actual**: ~80% (as of latest evidence snapshot)

**What's excluded from coverage**:
- Entrypoints (thin wrappers tested via E2E)
- Experimental modules (require optional dependencies)
- Test fixtures and utilities

### 4. Linting

```bash
make lint
# or: ruff check src tests --show-fixes
```

**Expected**: No lint errors (warnings are acceptable if documented)

### 5. Type Checking

```bash
make type
# or: mypy src/mlsdm
```

**Expected**: No type errors

### 6. Evidence Snapshot Test

```bash
pytest tests/unit/test_metrics_evidence_paths.py -q
```

**Checks**: `METRICS_SOURCE.md` references in-repo evidence paths (not CI URLs)

---

## Optional Extended Suites

These suites are run on `workflow_dispatch` or specific triggers, but not on every PR:

### Integration Tests

```bash
pytest tests/integration -q --disable-warnings --maxfail=1
```

**When to run**:
- Major feature PRs
- Before release
- On demand via workflow_dispatch

**What it tests**: Component interactions (LLM wrapper + memory, API + engine, etc.)

### Property Tests

```bash
pytest tests/property -q --maxfail=3
# or: make test (includes property tests)
```

**When to run**:
- Changes to core algorithms (memory, moral filter, rhythm)
- Before release
- On demand via workflow_dispatch

**What it tests**: Mathematical invariants, boundary conditions, randomized inputs

### End-to-End Tests

```bash
pytest tests/e2e -v
```

**When to run**:
- API changes
- Entrypoint changes
- Before release

**What it tests**: Full HTTP API workflows, service startup/shutdown, health checks

### Observability Tests

```bash
make test-memory-obs
# or: pytest tests/observability/ -v
```

**When to run**:
- Observability changes
- Before release
- Periodically (weekly)

**What it tests**: Metrics collection, logging, tracing, Aphasia instrumentation

### Performance Tests

```bash
make bench
# or: pytest benchmarks/test_neuro_engine_performance.py -v -s --tb=short
```

**When to run**:
- Core algorithm changes
- Before release
- Performance regression suspected

**What it tests**: API latency, throughput, memory footprint

### Chaos Tests

```bash
pytest tests/chaos/ -v
```

**When to run**:
- Resilience changes
- Before release
- On demand

**What it tests**: Behavior under adverse conditions (LLM failures, resource exhaustion)

---

## Benchmarks

### What's Measured

- **API Latency**: 95th percentile < 100ms (measured in `tests/perf/test_slo_api_endpoints.py`)
- **Memory Footprint**: ~29.37 MB for 20k vectors × 384 dimensions (measured in `benchmarks/measure_memory_footprint.py`)
- **Throughput**: 1000+ RPS concurrent processing (measured in `benchmarks/test_neuro_engine_performance.py`)

### How to Run Benchmarks

```bash
# Run performance benchmarks
make bench

# Check drift against baseline
make bench-drift
```

**Output**: `benchmark-metrics.json` with performance results

### What is NOT Audited Yet

- **Tail latency beyond p95**: p99, p99.9 latencies not yet tracked
- **Load testing at scale**: Full load tests (tests/load/) excluded from CI
- **GPU-accelerated benchmarks**: Experimental GPU features not benchmarked
- **Multi-node performance**: Distributed deployment performance not measured

---

## Reproducibility Guidelines

### Seed Usage

For reproducible tests, use the `deterministic_seed` fixture:

```python
from tests.utils.fixtures import deterministic_seed

def test_something(deterministic_seed):
    # Test will run with fixed seed for reproducibility
    pass
```

### Determinism Constraints

- **Memory ordering**: PELM uses stable sorting for deterministic retrieval
- **Random state**: All randomness controlled via `np.random.seed()` in tests
- **Timestamp mocking**: Tests use frozen time where needed (`freezegun`)
- **Moral filter**: Adaptive threshold based on deterministic EMA

### Known Non-Determinism

- **LLM responses**: Real LLM backends are non-deterministic (use stubs in tests)
- **Concurrent timing**: Exact timing of concurrent operations varies
- **OS scheduling**: Thread scheduling is non-deterministic (tests avoid timing assertions)

---

## Test Execution Commands (Quick Reference)

```bash
# PR minimum suite
python scripts/readiness_check.py
make test-fast
make coverage-gate
make lint
make type
pytest tests/unit/test_metrics_evidence_paths.py -q

# Full test suite
make test

# Specific test categories
pytest tests/unit -v
pytest tests/integration -v
pytest tests/e2e -v
pytest tests/property -v
pytest tests/observability -v

# Performance
make bench
make bench-drift

# Evaluation suites
make eval-moral_filter

# Evidence generation
make evidence
make verify-metrics
```

---

## CI Workflows

### Main CI Workflow

**File**: `.github/workflows/ci-neuro-cognitive-engine.yml`

**Jobs**:
- Dependency smoke test
- Unit tests
- Coverage gate (75% threshold)
- Linting (ruff)
- Type checking (mypy)
- Security scanning (semgrep)

### Evidence Workflow

**File**: `.github/workflows/readiness-evidence.yml`

**Jobs**:
- Unit tests (with artifacts)
- Coverage gate (with artifacts)
- Integration tests (workflow_dispatch only)
- Property tests (workflow_dispatch only)

### Property Tests Workflow

**File**: `.github/workflows/property-tests.yml`

**Trigger**: Manual (`workflow_dispatch`)

### Performance & Resilience Workflow

**File**: `.github/workflows/perf-resilience.yml`

**Jobs**:
- Performance benchmarks
- Memory footprint measurement
- Chaos tests

---

## Quality Gates

### PR Merge Requirements

1. ✅ All required checks pass (readiness, unit, coverage, lint, type)
2. ✅ No security findings (or suppressed with justification)
3. ✅ Code review approved
4. ✅ READINESS.md updated if code/tests/config/workflows changed

### Release Requirements

1. ✅ All PR merge requirements
2. ✅ Integration tests pass
3. ✅ Property tests pass
4. ✅ E2E tests pass
5. ✅ Performance benchmarks pass (no regression)
6. ✅ Evidence snapshot generated and verified
7. ✅ CHANGELOG.md updated
8. ✅ Release notes prepared

---

## Measuring Progress

### Coverage Progression

- **Current**: 80.04% (from latest evidence snapshot)
- **CI Threshold**: 75%
- **Target**: 85%+

**See**: `docs/METRICS_SOURCE.md` for evidence-based metrics

### Test Count

**Total**: 3,600+ tests (from JUnit evidence)

**Breakdown** (approximate):
- Unit: ~2,800 tests
- Integration: ~400 tests
- Property: ~150 tests
- E2E: ~100 tests
- Observability: ~80 tests
- Other: ~70 tests

**Exact counts**: Parse `artifacts/evidence/<date>/<sha>/pytest/junit.xml`

---

## Related Documentation

- **Testing Strategy**: [TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Comprehensive test approach
- **Test Strategy**: [TEST_STRATEGY.md](TEST_STRATEGY.md) - Suite organization
- **Metrics Source**: [METRICS_SOURCE.md](METRICS_SOURCE.md) - Evidence-based metrics
- **Runbook**: [RUNBOOK.md](RUNBOOK.md) - Troubleshooting CI failures
- **Contributing**: [../CONTRIBUTING.md](../CONTRIBUTING.md) - Development workflow

---

**Navigation**: [← Back to Documentation Index](README.md)
