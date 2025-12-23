# CI Map

| Workflow | Triggers | Purpose | Blocking (PR) | Artifacts |
| --- | --- | --- | --- | --- |
| ci-neuro-cognitive-engine | push/pull_request (main, feature/*) | Primary CI: lint, security scan, test matrix (3.10/3.11/3.12), coverage gate, e2e, effectiveness; benchmarks + neuro-engine-eval informational | Yes (all-ci-passed depends on lint/security/test/coverage/e2e/effectiveness). Benchmarks/eval informational only. | coverage-report, effectiveness-snapshot, benchmark-results, sapolsky-eval-results |
| ci-smoke | push/pull_request (main, feature/*) | Fast smoke, coverage gate, ablation smoke | Yes | coverage-report, ablation-report |
| readiness | push (main), pull_request | Runs readiness_check.py gate | Yes | none |
| readiness-evidence | pull_request, workflow_dispatch | Evidence run (uv-based deps smoke, unit, coverage gate) | Informational (evidence collection) | readiness-unit, readiness-coverage |
| property-tests | push/pull_request (core paths) | Property/invariant suites + counterexamples + invariant docs check | Yes | property-test-results, counterexamples-report, invariant-coverage |
| perf-resilience | push (main), pull_request, schedule (nightly), workflow_dispatch | Performance/resilience fast + SLO + comprehensive (nightly) | Fast/SLO jobs gate when run; comprehensive informational | resilience/perf junit artifacts |
| chaos-tests | schedule (daily 03:00 UTC), workflow_dispatch | Chaos engineering suites (memory/llm/network) | No (informational) | chaos-test-results (per Python) |
| sast-scan | push/pull_request (main) | Bandit, Semgrep, dependency audit, gitleaks | Yes | bandit/security SARIF, semgrep.sarif, dep-audit-report, secrets-scan-report |
| unicode-controls-check | push/pull_request | Trojan source / unicode control scan | Yes | none |
| citation-integrity | push/pull_request | Validate citation metadata | Yes | none |
| dependency-review | pull_request | GitHub dependency review gate | Yes | none |
| aphasia-ci | push/pull_request | Observability/aphasia focused checks | Yes | aphasia artifacts |
| prod-gate | push to release branches | Release promotion gate | Yes | none |
| release | workflow_dispatch | Publish release artifacts | On demand | release assets |

Dependency paths: pip uses `requirements.txt` + `pyproject.toml` (editable extras). uv workflows consume `uv.lock` + `pyproject.toml` (extras `dev`/`test`).
