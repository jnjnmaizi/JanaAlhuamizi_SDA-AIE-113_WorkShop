.PHONY: test lint run image golden hooks

test:
	python -m pytest --cov --cov-report=term-missing --cov-fail-under=80

lint:
	python -m ruff check src tests scripts/check_golden.py
	python -m mypy src/fraud_service
	lint-imports

run:
	python -m uvicorn fraud_service.api.app:create_app --factory --no-access-log

image:
	docker compose up --build -d

golden:
	python -m fraud_service.batch
	python scripts/check_golden.py scored.csv

hooks:
	pre-commit install
