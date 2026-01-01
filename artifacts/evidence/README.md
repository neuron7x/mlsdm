# Evidence Snapshots

## Policy

This directory contains committed evidence snapshots for reproducibility and auditability.

### Structure

```
evidence/
  YYYY-MM-DD/<git_sha>/
    manifest.json          # Metadata (schema_version, sha, date, commands, produced_files)
    coverage/
      coverage.xml         # Coverage report
    pytest/
      junit.xml            # JUnit test results
    pytest/
    logs/
      coverage_gate.log    # coverage gate stdout/stderr
      unit_tests.log       # unit test stdout/stderr
    benchmarks/            # Optional if benchmarks are collected
      benchmark-metrics.json
```

### Rules

1. **Small files only** — Keep evidence compact; no large dumps or binary blobs.
2. **No secrets** — Never commit credentials, tokens, .env files, or API keys.
3. **Dated folders** — Each snapshot lives in a dated subfolder; do NOT overwrite previous snapshots.
4. **Reproducible** — Evidence is regenerated via `make evidence` (runs `python scripts/evidence/capture_evidence.py`).
5. **Read-only archive** — Treat committed snapshots as immutable historical records.

### Regenerating Evidence

```bash
make evidence
```

This runs `uv run python scripts/evidence/capture_evidence.py` which:
- Creates a new dated folder under `artifacts/evidence/`
- Runs the coverage gate and captures `coverage.xml`
- Runs unit tests with JUnit output
- Captures command logs and writes `manifest.json`

### Retention

Snapshots are kept for historical reference. To clean up old snapshots, manually delete
dated folders that are no longer needed for audit trails.
