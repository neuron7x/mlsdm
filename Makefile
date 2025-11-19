.PHONY: test lint type cov

test:
	pytest src/tests/ --cov=src --cov-report=html --cov-fail-under=90

lint:
	ruff check . --fix

type:
	mypy . --strict

cov:
	pytest --cov=src --cov-report=term-missing
