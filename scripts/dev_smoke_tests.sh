#!/usr/bin/env bash
# MLSDM Development Smoke Tests
# Runs quick validation tests to ensure local dev environment is working
#
# Usage: ./scripts/dev_smoke_tests.sh
#
# This script matches CI test execution for consistency.
# Run this before pushing changes to catch issues early.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "MLSDM Development Smoke Tests"
echo "=========================================="
echo ""

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if we're in a virtual environment (recommended)
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
    echo -e "${YELLOW}⚠️  Warning: Not running in a virtual environment${NC}"
    echo "   Consider activating a venv for isolation"
else
    echo -e "${GREEN}✓ Running in virtual environment: $VIRTUAL_ENV${NC}"
fi

echo ""
echo -e "${YELLOW}Setting up environment...${NC}"
# Set PYTHONPATH to src directory for imports
export PYTHONPATH="${PWD}/src:${PYTHONPATH:-}"
export DISABLE_RATE_LIMIT=1
export LLM_BACKEND=local_stub

echo "PYTHONPATH=$PYTHONPATH"
echo ""

# Run pytest with the same flags as CI
echo -e "${YELLOW}Running test suite (ignoring load tests)...${NC}"
if python -m pytest -q --ignore=tests/load --tb=short; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo -e "✓ All smoke tests passed!"
    echo -e "==========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}=========================================="
    echo -e "✗ Some tests failed"
    echo -e "==========================================${NC}"
    exit 1
fi
