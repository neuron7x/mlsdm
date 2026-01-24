.PHONY: test test-fast coverage-gate verify-metrics verify-security-skip verify-docs lint type cov bench bench-drift help run-dev run-cloud-local run-agent health-check eval-moral_filter test-memory-obs \
        readiness-preview readiness-apply \
        build-package test-package docker-build-neuro-engine docker-run-neuro-engine docker-smoke-neuro-engine \
        docker-compose-up docker-compose-down lock sync lock-deps evidence iteration-metrics

export PYTHONPATH := $(PYTHONPATH):$(CURDIR)/src
ITERATION_METRICS_PATH ?= artifacts/tmp/iteration-metrics.jsonl
EVIDENCE_INPUTS_PATH ?= artifacts/tmp/evidence-inputs.json

help:
	@echo "MLSDM Governed Cognitive Memory - Development Commands"
	@echo ""
	@echo "Testing & Linting:"
	@echo "  make test          - Run all tests (uses pytest.ini config)"
	@echo "  make test-fast     - Run fast unit tests (excludes slow/comprehensive)"
	@echo "  make coverage-gate - Run coverage gate with threshold check"
	@echo "  make verify-metrics - Validate latest evidence snapshot integrity"
	@echo "  make verify-security-skip - Verify security skip path invariants and docs examples"
	@echo "  make verify-docs    - Verify documentation contracts against code defaults"
	@echo "  make lint          - Run ruff linter on src and tests"
	@echo "  make type          - Run mypy type checker on src/mlsdm"
	@echo "  make cov           - Run tests with coverage report"
	@echo "  make bench         - Run performance benchmarks (matches CI)"
	@echo "  make bench-drift   - Check benchmark results against baseline"
	@echo ""
	@echo "Package Building:"
	@echo "  make build-package  - Build wheel and sdist distributions"
	@echo "  make test-package   - Test package installation in fresh venv"
	@echo ""
	@echo "Dependency Management:"
	@echo "  make sync           - Install dependencies from uv.lock (recommended)"
	@echo "  make lock           - Update uv.lock with latest compatible versions"
	@echo "  make lock-deps      - Lock dependencies with pip-compile (generates hashed requirements)"
	@echo "  make changelog      - Generate changelog from conventional commits"
	@echo "  make validate-api-contract - Validate API contract against baseline"
	@echo "  make update-api-baseline   - Update API contract baseline"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build-neuro-engine  - Build neuro-engine Docker image"
	@echo "  make docker-run-neuro-engine    - Run neuro-engine container locally"
	@echo "  make docker-smoke-neuro-engine  - Run smoke test on container"
	@echo "  make docker-compose-up          - Start local stack with docker-compose"
	@echo "  make docker-compose-down        - Stop local stack"
	@echo ""
	@echo "Observability Tests:"
	@echo "  make test-memory-obs - Run memory observability tests"
	@echo ""
	@echo "Readiness:"
	@echo "  make readiness-preview TITLE=\"Message\" [BASE_REF=origin/main] - Preview readiness change log update"
	@echo "  make readiness-apply   TITLE=\"Message\" [BASE_REF=origin/main] - Apply readiness change log update"
	@echo ""
	@echo "Evaluations:"
	@echo "  make eval-moral_filter - Run moral filter evaluation suite"
	@echo ""
	@echo "Runtime Modes:"
	@echo "  make run-dev        - Start development server (hot reload, debug logging)"
	@echo "  make run-cloud-local - Start local production server (multiple workers)"
	@echo "  make run-agent      - Start agent/API server (for LLM integration)"
	@echo "  make health-check   - Run health check"
	@echo ""
	@echo "Note: These commands match what CI runs. Run them before pushing."

# Testing & Linting
test:
	pytest --ignore=tests/load

test-fast:
	@echo "Running fast unit tests (excluding slow/comprehensive)..."
	pytest tests/unit tests/state -m "not slow and not comprehensive" -q --tb=short

coverage-gate:
	@echo "Running coverage gate..."
	./coverage_gate.sh
	@if [ ! -f coverage.xml ]; then \
		echo "ERROR: coverage.xml was not generated"; \
		exit 1; \
	fi
	@echo "✓ coverage.xml generated successfully"

verify-metrics:
	@LATEST_SNAPSHOT=$$(ls -1d artifacts/evidence/*/* 2>/dev/null | LC_ALL=C sort | tail -n 1); \
	if [ -z "$$LATEST_SNAPSHOT" ]; then \
		echo "No evidence snapshot found under artifacts/evidence"; \
		exit 1; \
	fi; \
	echo "Validating evidence snapshot: $$LATEST_SNAPSHOT"; \
	python scripts/evidence/verify_evidence_snapshot.py --evidence-dir "$$LATEST_SNAPSHOT"

verify-security-skip:
	@python scripts/verify_security_skip_invariants.py
	@python scripts/verify_docs_examples.py

verify-docs:
	@python scripts/verify_docs_contracts.py
	@python scripts/verify_docs_examples.py
	@python scripts/verify_docs_claims_against_code.py

lint:
	@echo "Running ruff linter (src + tests)..."
	@ruff check src tests --show-fixes || (echo "❌ Lint failed.  Run 'ruff check src tests --fix' to auto-fix" && exit 1)

type:
	mypy src/mlsdm

cov:
	pytest --ignore=tests/load --cov=src --cov-report=html --cov-report=term-missing

bench:
	@echo "Running performance benchmarks..."
	pytest benchmarks/test_neuro_engine_performance.py -v -s --tb=short

bench-drift:
	@echo "Checking benchmark drift against baseline..."
	@if [ -f benchmark-metrics.json ]; then \
		python scripts/check_benchmark_drift.py benchmark-metrics.json; \
	else \
		echo "Error: benchmark-metrics.json not found. Run 'make bench' first."; \
		exit 1; \
	fi

TITLE ?=
BASE_REF ?= origin/main

readiness-preview:
	python scripts/readiness/changelog_generator.py --title "$(TITLE)" --base-ref "$(BASE_REF)" --mode preview

readiness-apply:
	python scripts/readiness/changelog_generator.py --title "$(TITLE)" --base-ref "$(BASE_REF)" --mode apply

# Package Building
build-package:
	python -m build

test-package:
	@echo "Testing package installation in fresh venv..."
	rm -rf /tmp/mlsdm-test-venv
	python -m venv /tmp/mlsdm-test-venv
	/tmp/mlsdm-test-venv/bin/pip install --upgrade pip -q
	/tmp/mlsdm-test-venv/bin/pip install dist/*.whl -q
	/tmp/mlsdm-test-venv/bin/python -c "from mlsdm import __version__, create_llm_wrapper; print(f'MLSDM v{__version__} installed OK')"
	rm -rf /tmp/mlsdm-test-venv
	@echo "✓ Package test passed"

# Dependency Management
sync:
	@echo "Installing dependencies from uv.lock..."
	uv sync

lock:
	@echo "Updating uv.lock with latest compatible versions..."
	uv lock --upgrade
	@echo "✓ uv.lock updated"

lock-deps:
	@echo "Locking dependencies with pip-compile..."
	@echo "This will generate requirements.txt with all transitive dependencies pinned and hashed."
	@pip-compile pyproject.toml --generate-hashes --output-file=requirements.txt --verbose
	@echo "✓ requirements.txt generated with hashes"
	@echo ""
	@echo "Generating requirements-dev.txt with dev dependencies..."
	@pip-compile pyproject.toml --extra=dev --generate-hashes --output-file=requirements-dev.txt --verbose
	@echo "✓ requirements-dev.txt generated with hashes"
	@echo ""
	@echo "Dependency lock complete. Commit the updated files to git."

# Changelog Generation
changelog:
	@echo "Generating changelog from conventional commits..."
	@if [ -z "$(PREV_TAG)" ]; then \
		PREV_TAG=$$(git describe --tags --abbrev=0 2>/dev/null || echo ""); \
	fi; \
	if [ -z "$$PREV_TAG" ]; then \
		echo "No previous tag found, generating changelog from all commits"; \
		RANGE="HEAD"; \
	else \
		echo "Generating changelog from $$PREV_TAG to HEAD"; \
		RANGE="$$PREV_TAG..HEAD"; \
	fi; \
	echo "## [Unreleased] - $$(date +%Y-%m-%d)" > CHANGELOG.fragment.md; \
	echo "" >> CHANGELOG.fragment.md; \
	FEATURES=$$(git log $$RANGE --pretty=format:"%s" 2>/dev/null | grep -E "^feat(\(.*\))?:" | sed 's/^feat\([^:]*\): /- /' || true); \
	if [ -n "$$FEATURES" ]; then \
		echo "### ✨ Features" >> CHANGELOG.fragment.md; \
		echo "$$FEATURES" >> CHANGELOG.fragment.md; \
		echo "" >> CHANGELOG.fragment.md; \
	fi; \
	FIXES=$$(git log $$RANGE --pretty=format:"%s" 2>/dev/null | grep -E "^fix(\(.*\))?:" | sed 's/^fix\([^:]*\): /- /' || true); \
	if [ -n "$$FIXES" ]; then \
		echo "### 🐛 Bug Fixes" >> CHANGELOG.fragment.md; \
		echo "$$FIXES" >> CHANGELOG.fragment.md; \
		echo "" >> CHANGELOG.fragment.md; \
	fi; \
	DOCS=$$(git log $$RANGE --pretty=format:"%s" 2>/dev/null | grep -E "^docs(\(.*\))?:" | sed 's/^docs\([^:]*\): /- /' || true); \
	if [ -n "$$DOCS" ]; then \
		echo "### 📚 Documentation" >> CHANGELOG.fragment.md; \
		echo "$$DOCS" >> CHANGELOG.fragment.md; \
		echo "" >> CHANGELOG.fragment.md; \
	fi; \
	PERF=$$(git log $$RANGE --pretty=format:"%s" 2>/dev/null | grep -E "^perf(\(.*\))?:" | sed 's/^perf\([^:]*\): /- /' || true); \
	if [ -n "$$PERF" ]; then \
		echo "### ⚡ Performance" >> CHANGELOG.fragment.md; \
		echo "$$PERF" >> CHANGELOG.fragment.md; \
		echo "" >> CHANGELOG.fragment.md; \
	fi; \
	SECURITY=$$(git log $$RANGE --pretty=format:"%s" 2>/dev/null | grep -E "^(security|sec)(\(.*\))?:" | sed 's/^sec\(urity\)\?\([^:]*\): /- /' || true); \
	if [ -n "$$SECURITY" ]; then \
		echo "### 🔒 Security" >> CHANGELOG.fragment.md; \
		echo "$$SECURITY" >> CHANGELOG.fragment.md; \
		echo "" >> CHANGELOG.fragment.md; \
	fi; \
	CHORES=$$(git log $$RANGE --pretty=format:"%s" 2>/dev/null | grep -E "^chore(\(.*\))?:" | sed 's/^chore\([^:]*\): /- /' || true); \
	if [ -n "$$CHORES" ]; then \
		echo "### 🔧 Maintenance" >> CHANGELOG.fragment.md; \
		echo "$$CHORES" >> CHANGELOG.fragment.md; \
		echo "" >> CHANGELOG.fragment.md; \
	fi; \
	cat CHANGELOG.fragment.md
	@echo ""
	@echo "✓ Changelog fragment generated: CHANGELOG.fragment.md"
	@echo "Review and prepend to CHANGELOG.md manually, or wait for automated generation on release."

# API Contract Validation
validate-api-contract:
	@echo "Validating API contract against baseline..."
	@DISABLE_RATE_LIMIT=1 python scripts/export_openapi.py --output /tmp/openapi-current.json
	@python scripts/openapi_contract_check.py docs/openapi-baseline.json /tmp/openapi-current.json
	@echo "✓ API contract validation passed"

update-api-baseline:
	@echo "Updating API contract baseline..."
	@DISABLE_RATE_LIMIT=1 python scripts/export_openapi.py --output docs/openapi-baseline.json
	@echo "✓ API baseline updated: docs/openapi-baseline.json"
	@echo "Review changes and commit the updated baseline."

# Docker
DOCKER_IMAGE_NAME ?= ghcr.io/neuron7x/mlsdm-neuro-engine
DOCKER_IMAGE_TAG ?= latest

docker-build-neuro-engine:
	docker build -f Dockerfile.neuro-engine-service -t $(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG) .

docker-run-neuro-engine:
	docker run --rm -p 8000:8000 \
		-e LLM_BACKEND=local_stub \
		-e ENABLE_METRICS=true \
		--name mlsdm-neuro-engine \
		$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)

docker-smoke-neuro-engine:
	@echo "Starting container for smoke test..."
	docker run -d --rm -p 8000:8000 \
		-e LLM_BACKEND=local_stub \
		-e DISABLE_RATE_LIMIT=1 \
		--name mlsdm-smoke-test \
		$(DOCKER_IMAGE_NAME):$(DOCKER_IMAGE_TAG)
	@echo "Waiting for container to start..."
	@sleep 10
	@echo "Running smoke tests..."
	curl -s http://localhost:8000/health | grep -q "healthy" && echo "✓ Health check passed" || (echo "✗ Health check failed" && docker stop mlsdm-smoke-test && exit 1)
	curl -s http://localhost:8000/health/ready | grep -q "ready" && echo "✓ Readiness check passed" || (echo "✗ Readiness check failed" && docker stop mlsdm-smoke-test && exit 1)
	curl -s -X POST http://localhost:8000/generate -H "Content-Type: application/json" -d '{"prompt": "Hello"}' | grep -q "response" && echo "✓ Generate endpoint passed" || (echo "✗ Generate test failed" && docker stop mlsdm-smoke-test && exit 1)
	@echo "Stopping container..."
	docker stop mlsdm-smoke-test
	@echo "✓ All smoke tests passed"

docker-compose-up:
	docker compose -f docker/docker-compose.yaml up -d

docker-compose-down:
	docker compose -f docker/docker-compose.yaml down

# Observability Tests
test-memory-obs:
	pytest tests/observability/test_memory_observability.py -v

# Runtime Modes
run-dev:
	mlsdm serve --mode dev --reload --log-level debug --disable-rate-limit

run-cloud-local:
	mlsdm serve --mode cloud-prod

run-agent:
	mlsdm serve --mode agent-api

health-check:
	python -m mlsdm.entrypoints.health

# Evaluation Suites
eval-moral_filter:
	python -m evals.moral_filter_runner

# Evidence Snapshot
iteration-metrics:
	@echo "Generating deterministic iteration metrics..."
	@mkdir -p $(dir $(ITERATION_METRICS_PATH))
	python scripts/eval/generate_iteration_metrics.py --out $(ITERATION_METRICS_PATH)

evidence: iteration-metrics
	@mkdir -p $(dir $(EVIDENCE_INPUTS_PATH))
	@echo '{"iteration_metrics": "$(ITERATION_METRICS_PATH)"}' > $(EVIDENCE_INPUTS_PATH)
	@echo "Capturing evidence snapshot..."
	DISABLE_UV_RUN=1 python scripts/evidence/capture_evidence.py --mode build --inputs $(EVIDENCE_INPUTS_PATH)
	@echo "Verifying captured evidence snapshot..."
	$(MAKE) verify-metrics
