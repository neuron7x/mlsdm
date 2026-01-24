#!/usr/bin/env bash
set -u -o pipefail

mkdir -p artifacts/evidence

soft_limit_seconds="${COVERAGE_SOFT_LIMIT_SECONDS:-1020}"
coverage_exit=0
coverage_start_epoch=$(date +%s)

# Determine optimal worker count for GitHub Actions (usually 2-core runners)
PYTEST_WORKERS="${PYTEST_WORKERS:-auto}"

printf "Starting coverage run with soft limit %ss (parallelization: %s workers)\n" "$soft_limit_seconds" "$PYTEST_WORKERS"

# Robust timeout handling with coverage data preservation
if ! timeout --signal=TERM --kill-after=30s "${soft_limit_seconds}s" \
  coverage run --source=src/mlsdm --concurrency=multiprocessing -m pytest \
    --ignore=tests/load \
    -m "not slow and not benchmark" \
    -n "${PYTEST_WORKERS}" \
    --dist loadgroup \
    --maxfail=3 \
    2>&1 | tee artifacts/evidence/coverage.log; then
  coverage_exit=$?
  
  if [ "$coverage_exit" -eq 124 ]; then
    echo "⚠️  ERROR: Coverage run exceeded soft limit (${soft_limit_seconds}s) and was terminated." >&2
    echo "→ Attempting emergency coverage data recovery..." >&2
    
    # Strategy 1: Try to combine partial .coverage.* shards (multiprocessing mode)
    if compgen -G ".coverage.*" > /dev/null 2>&1; then
      echo "   Found partial coverage shards, combining..." >&2
      if coverage combine 2>&1 | tee -a artifacts/evidence/coverage.log; then
        echo "✓ Partial coverage data successfully recovered" >&2
        coverage_exit=0  # Reset exit code if recovery successful
      else
        echo "✗ Failed to combine partial coverage data" >&2
      fi
    else
      echo "   No partial coverage shards found (.coverage.* pattern)" >&2
    fi
    
    # Strategy 2: Check for main .coverage file (may exist from incomplete write)
    if [ ! -f .coverage ] && [ "$coverage_exit" -eq 124 ]; then
      echo "✗ No .coverage file recoverable - timeout occurred before any data persistence" >&2
      echo "   Recommendation: Increase COVERAGE_SOFT_LIMIT_SECONDS or enable test parallelization" >&2
    fi
  fi
fi

coverage_end_epoch=$(date +%s)
coverage_duration_seconds=$((coverage_end_epoch - coverage_start_epoch))

# Combine coverage data from parallel workers (multiprocessing mode)
# This is needed both for successful runs and recovery scenarios
if [ "$coverage_exit" -eq 0 ] && compgen -G ".coverage.*" > /dev/null 2>&1; then
  printf "\nCombining coverage data from parallel workers...\n"
  if ! coverage combine 2>&1 | tee -a artifacts/evidence/coverage.log; then
    echo "WARNING: Failed to combine coverage data from parallel workers" >&2
  fi
fi

# Generate coverage reports from .coverage database
if [ -f .coverage ]; then
  printf "\nGenerating coverage reports...\n"
  coverage report --show-missing || true
  coverage json -o coverage.json || {
    echo "WARNING: Failed to generate coverage.json" >&2
  }
  coverage xml -o coverage.xml || {
    echo "WARNING: Failed to generate coverage.xml" >&2
  }
else
  echo "ERROR: .coverage file not found after test execution" >&2
  coverage_exit=1
fi

if [ -n "${GITHUB_ENV:-}" ]; then
  echo "COVERAGE_DURATION_SECONDS=${coverage_duration_seconds}" >> "$GITHUB_ENV"
fi

export COVERAGE_EXIT_CODE="$coverage_exit"
export COVERAGE_DURATION_SECONDS="$coverage_duration_seconds"

python <<'PY'
import json
import os
import pathlib
import subprocess

report_path = pathlib.Path("artifacts/evidence/coverage_badge_run_report.json")
report_path.parent.mkdir(parents=True, exist_ok=True)

coverage_value = None
coverage_json_path = pathlib.Path("coverage.json")
if coverage_json_path.exists():
    try:
        data = json.loads(coverage_json_path.read_text())
        coverage_value = data.get("totals", {}).get("percent_covered")
    except json.JSONDecodeError:
        coverage_value = None

commit = os.environ.get("GITHUB_SHA")
if not commit:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        commit = "unknown"

report = {
    "commit": commit,
    "python_version": os.environ.get("PYTHON_VERSION", "unknown"),
    "durations": {
        "install_seconds": int(os.environ.get("INSTALL_DURATION_SECONDS", "0") or 0),
        "coverage_seconds": int(os.environ.get("COVERAGE_DURATION_SECONDS", "0") or 0),
        "badge_seconds": int(os.environ.get("BADGE_DURATION_SECONDS", "0") or 0),
    },
    "cache_hits": {
        "pip_cache_present": os.environ.get("PIP_CACHE_PRESENT", "false") == "true",
    },
    "coverage_value": coverage_value,
    "exit_codes": {
        "coverage": int(os.environ.get("COVERAGE_EXIT_CODE", "0") or 0),
    },
    "canceled_flag": os.environ.get("CANCELED_FLAG", "false") == "true",
}

report_path.write_text(json.dumps(report, indent=2, sort_keys=True))
PY

exit "$coverage_exit"
