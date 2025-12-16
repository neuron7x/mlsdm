#!/bin/bash
# ============================================================================
# coverage_gate.sh - Coverage Gate Script for MLSDM
# ============================================================================
# SPDX-License-Identifier: MIT
#
# This script runs tests with coverage measurement and enforces a minimum
# coverage threshold. It is designed to work in CI and locally.
#
# Usage:
#   ./coverage_gate.sh               # Uses default threshold (65%)
#   COVERAGE_MIN=80 ./coverage_gate.sh  # Uses 80% threshold
#
# Exit codes:
#   0 - Tests passed and coverage meets threshold
#   1 - Tests failed or coverage below threshold
#
# Environment Variables:
#   COVERAGE_MIN - Minimum coverage percentage required (default: 65)
#   PYTEST_ARGS  - Additional arguments to pass to pytest
# ============================================================================

set -euo pipefail

# Default coverage threshold (can be overridden via environment variable)
# Set to match CI gate threshold for consistency
# CI workflow uses --cov-fail-under=65 in ci-neuro-cognitive-engine.yml
COVERAGE_MIN="${COVERAGE_MIN:-65}"

# Additional pytest arguments (can be extended via environment variable)
PYTEST_ARGS="${PYTEST_ARGS:-}"

# Colors for output (disabled if not a terminal)
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

echo "========================================================================"
echo "MLSDM Coverage Gate"
echo "========================================================================"
echo ""
echo "Configuration:"
echo "  COVERAGE_MIN: ${COVERAGE_MIN}%"
echo "  PYTEST_ARGS:  ${PYTEST_ARGS:-<none>}"
echo ""

# Change to repository root (script location)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "Working directory: $(pwd)"
echo ""

# Run pytest with coverage (canonical command used in CI)
echo "========================================================================"
echo "Running tests with coverage..."
echo "========================================================================"
echo ""

# shellcheck disable=SC2086
python -m pytest tests \
    --ignore=tests/load \
    --cov=src/mlsdm \
    --cov-report=xml:coverage.xml \
    --cov-report=term-missing \
    --cov-fail-under="${COVERAGE_MIN}" \
    -m "not slow and not benchmark" \
    -v \
    --tb=short \
    $PYTEST_ARGS

echo ""
echo "========================================================================"
printf "${GREEN}✓ COVERAGE GATE PASSED (threshold %s%%)${NC}\n" "${COVERAGE_MIN}"
echo "========================================================================"
