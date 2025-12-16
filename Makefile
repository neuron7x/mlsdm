.PHONY: test lint type cov coverage-gate ci-core smoke e2e effectiveness bench bench-drift help run-dev run-cloud-local run-agent health-check eval-moral_filter test-memory-obs \
        build-package test-package docker-build-neuro-engine docker-run-neuro-engine docker-smoke-neuro-engine \
        docker-compose-up docker-compose-down

export PYTHONPATH := $(PYTHONPATH):$(CURDIR)/src

help:
	@echo "MLSDM Governed Cognitive Memory - Development Commands"
	@echo ""
	@echo "Testing & Linting:"
	@echo "  make test     - Run all tests (uses pytest.ini config)"
	@echo "  make lint     - Run ruff linter on src and tests"
	@echo "  make type     - Run mypy type checker on src/mlsdm"
	@echo "  make coverage-gate - Run coverage gate (65% threshold, matches CI)"
	@echo "  make cov      - Alias for coverage-gate"
	@echo "  make ci-core  - Run lint, type, test, and coverage gate in sequence"
	@echo "  make bench    - Run performance benchmarks (matches CI)"
	@echo "  make bench-drift - Check benchmark results against baseline"
	@echo "  make smoke    - Run fast smoke test suite"
	@echo "  make e2e      - Run end-to-end tests (not slow)"
	@echo "  make effectiveness - Run effectiveness validation with SLO checks"
	@echo ""
	@echo "Package Building:"
	@echo "  make build-package  - Build wheel and sdist distributions"
	@echo "  make test-package   - Test package installation in fresh venv"
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
	pytest -q --ignore=tests/load

lint:
	ruff check src tests

type:
	mypy src/mlsdm

cov:
	$(MAKE) coverage-gate

coverage-gate:
	./coverage_gate.sh

ci-core:
	$(MAKE) lint
	$(MAKE) type
	$(MAKE) test
	$(MAKE) coverage-gate

smoke:
	pytest tests/unit/ -v -m "not slow" --tb=short -q --maxfail=5

e2e:
	pytest tests/e2e -v -m "not slow" --tb=short

effectiveness:
	python scripts/run_effectiveness_suite.py --validate-slo

bench:
	@echo "Running performance benchmarks..."
	bash -c 'set -o pipefail; pytest benchmarks/test_neuro_engine_performance.py -v -s --tb=short --junitxml=benchmark-results.xml 2>&1 | tee benchmark-output.txt'
	python -c "import re, json, os; from datetime import datetime, timezone; \
content=open('benchmark-output.txt').read(); \
metrics={'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'commit': os.environ.get('GITHUB_SHA','unknown')[:8], 'metrics': {}}; \
p95=[float(x) for x in re.findall(r'P95:\\s+([0-9.]+)ms', content)]; \
metrics['metrics']['p95_latencies_ms']=p95; \
metrics['metrics']['max_p95_ms']=max(p95) if p95 else None; \
metrics['slo_compliant']='SLO met' in content; \
json.dump(metrics, open('benchmark-metrics.json','w'), indent=2); \
print(f'Extracted metrics: {json.dumps(metrics, indent=2)}')"
	@if grep -q "SLO met" benchmark-output.txt; then \
		echo "✅ All SLO targets met"; \
		if [ -n "$$GITHUB_OUTPUT" ]; then echo "slo_status=passed" >> "$$GITHUB_OUTPUT"; fi; \
	else \
		echo "⚠️ Some SLO targets may not have been verified"; \
		if [ -n "$$GITHUB_OUTPUT" ]; then echo "slo_status=unknown" >> "$$GITHUB_OUTPUT"; fi; \
	fi

bench-drift:
	@echo "Checking benchmark drift against baseline..."
	@if [ -f benchmark-metrics.json ]; then \
		python scripts/check_benchmark_drift.py benchmark-metrics.json; \
	else \
		echo "Error: benchmark-metrics.json not found. Run 'make bench' first."; \
		exit 1; \
	fi

# Package Building
build-package:
	python -m build

test-package:
	@echo "Testing package installation in fresh venv..."
	rm -rf /tmp/mlsdm-test-venv
	python -m venv /tmp/mlsdm-test-venv
	/tmp/mlsdm-test-venv/bin/pip install --upgrade pip -q
	/tmp/mlsdm-test-venv/bin/pip install dist/*.whl -q
	/tmp/mlsdm-test-venv/bin/python scripts/test_package_install.py
	rm -rf /tmp/mlsdm-test-venv
	@echo "✓ Package test passed"

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
	python -m mlsdm.entrypoints.dev

run-cloud-local:
	python -m mlsdm.entrypoints.cloud

run-agent:
	python -m mlsdm.entrypoints.agent

health-check:
	python -m mlsdm.entrypoints.health

# Evaluation Suites
eval-moral_filter:
	python -m evals.moral_filter_runner
