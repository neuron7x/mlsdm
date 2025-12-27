# Metrics Source of Truth

**Last Updated**: December 27, 2025
**Purpose**: Single source for test coverage and quality metrics to prevent documentation drift.

---

## Evidence Snapshots

Metrics are sourced from **committed evidence snapshots** in the repository for reproducibility.

| Artifact | Path |
|----------|------|
| **Coverage Report** | `artifacts/evidence/<date>/<sha>/coverage/coverage.xml` |
| **JUnit Test Results** | `artifacts/evidence/<date>/<sha>/pytest/junit.xml` |
| **Benchmark Metrics** | `artifacts/evidence/<date>/<sha>/benchmarks/benchmark-metrics.json` |
| **Raw Latency Samples** | `artifacts/evidence/<date>/<sha>/benchmarks/raw_neuro_engine_latency.json` (capped at 2000 samples per scenario) |
| **Memory Footprint** | `artifacts/evidence/<date>/<sha>/memory/memory_footprint.json` |
| **Manifest** | `artifacts/evidence/<date>/<sha>/manifest.json` |

To regenerate evidence locally:

```bash
make evidence
```

---

## Coverage Metrics

| Metric | Source |
|--------|--------|
| **CI Coverage Threshold** | `coverage_gate.sh` + `.github/workflows/ci-neuro-cognitive-engine.yml` |
| **Baseline Coverage Percent** | `benchmarks/baseline.json` (`metrics.coverage_percent`, derived from committed evidence) |

---

## Test Metrics

Test counts are derived from committed JUnit evidence and tracked in the baseline:

| Metric | Source |
|--------|--------|
| **Test Totals / Failures** | `benchmarks/baseline.json` (`metrics.unit_tests_total`, `metrics.test_failures`) derived from `artifacts/evidence/<date>/<sha>/pytest/junit.xml` |

---

## Benchmark Metrics

Performance metrics are captured in the evidence snapshot:

| Metric | Source |
|--------|--------|
| **Benchmark Results** | `artifacts/evidence/<date>/<sha>/benchmarks/benchmark-metrics.json` |
| **Raw Latency Samples (capped)** | `artifacts/evidence/<date>/<sha>/benchmarks/raw_neuro_engine_latency.json` |
| **Baseline** | `benchmarks/baseline.json` |

To check for benchmark drift:

```bash
python scripts/check_benchmark_drift.py artifacts/evidence/<date>/<sha>/benchmarks/benchmark-metrics.json
```

---

## How CI enforces drift

CI runs the following steps to keep evidence auditable:

```bash
make evidence
python scripts/evidence/verify_evidence_snapshot.py --evidence-dir <path produced above>
python scripts/evidence/check_drift.py --baseline benchmarks/baseline.json --evidence-dir <path produced above>
```

The evidence directory from `make evidence` is uploaded as a workflow artifact for audit.

---

## Updating This Document

When evidence is regenerated:

1. Run `make evidence` to capture a new snapshot
2. Commit the new evidence folder under `artifacts/evidence/`
3. Update the "Last Updated" date above
4. If coverage exceeds threshold by 5%+ for 2+ releases, consider raising the threshold

---

## Related Documentation

- [TESTING_GUIDE.md](../TESTING_GUIDE.md) - How to write and run tests
- [CI_GUIDE.md](../CI_GUIDE.md) - CI/CD configuration overview
- [TEST_STRATEGY.md](../TEST_STRATEGY.md) - Test organization and priorities
- [Evidence README](../artifacts/evidence/README.md) - Evidence snapshot policy
