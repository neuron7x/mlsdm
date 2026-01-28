# Quality Index (SSOT)

This document enumerates the system-of-record artifacts used to define quality
claims for the MLSDM repository. It is intentionally declarative and does not
assert metrics beyond what the referenced artifacts encode.

## Canonical Sources of Truth

* `docs/QUALITY_INDEX.md` (this file)
* `quality/mutation_baseline.json`
* `specs/tla/**` (with code-contract mappings)
* `tests/conftest.py` (markers, Hypothesis profiles, taxonomy guards)
* All guard tests (profile, determinism, taxonomy)

## Verification Entry Points

* `make check`
* `make test`
* `make mutation-check`
