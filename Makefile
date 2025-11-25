.PHONY: test lint type cov help benchmark benchmark-json benchmark-table

help:
	@echo "MLSDM Governed Cognitive Memory - Development Commands"
	@echo ""
	@echo "make test           - Run all tests (uses pytest.ini config)"
	@echo "make lint           - Run ruff linter on src and tests"
	@echo "make type           - Run mypy type checker on src/mlsdm"
	@echo "make cov            - Run tests with coverage report"
	@echo "make benchmark      - Run performance benchmarks (console output)"
	@echo "make benchmark-json - Run benchmarks with JSON output"
	@echo "make benchmark-table- Run benchmarks with Markdown table output"
	@echo ""
	@echo "Note: These commands match what CI runs. Run them before pushing."

test:
	pytest --ignore=tests/load

lint:
	ruff check src tests benchmarks

type:
	mypy src/mlsdm

cov:
	pytest --ignore=tests/load --cov=src --cov-report=html --cov-report=term-missing

benchmark:
	python benchmarks/test_neuro_engine_performance.py --output console

benchmark-json:
	python benchmarks/test_neuro_engine_performance.py --output json

benchmark-table:
	python benchmarks/test_neuro_engine_performance.py --output table
