# Test Hygiene Coverage Evidence

## Reproduction Commands

1. Run the coverage gate (generates `coverage.xml`):

```bash
bash ./coverage_gate.sh
```

2. Generate the deterministic module summary JSON:

```bash
python scripts/test_hygiene/coverage_summary.py \
  --coverage-xml coverage.xml \
  --out artifacts/test_hygiene/coverage_summary.json
```

3. Determinism check (byte-identical summaries):

```bash
python scripts/test_hygiene/coverage_summary.py \
  --coverage-xml coverage.xml \
  --out artifacts/test_hygiene/coverage_summary.json
python scripts/test_hygiene/coverage_summary.py \
  --coverage-xml coverage.xml \
  --out artifacts/test_hygiene/coverage_summary.json
cmp artifacts/test_hygiene/coverage_summary.json artifacts/test_hygiene/coverage_summary.json
```

## Targeted Modules (Baseline Coverage Rationale)

* `src/mlsdm/api/schemas.py` (baseline 0% coverage from coverage gate; now covered by schema validation tests).
* `src/mlsdm/config/architecture_manifest.py` (baseline 0% coverage; now covered by manifest invariants tests).
* `src/mlsdm/policy/check.py` (baseline 0% coverage; now covered by policy stage and path resolution tests).
* `src/mlsdm/policy/validation.py` (baseline 0% coverage; now covered by validation error/warning path tests).
* `src/mlsdm/cli/main.py` (baseline 0% coverage; now covered by CLI formatter and run harness tests).
* `src/mlsdm/cli/__main__.py` (baseline 0% coverage; now covered by module entrypoint test).
