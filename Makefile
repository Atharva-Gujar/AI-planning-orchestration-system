.PHONY: help install test coverage lint format clean run-examples

help:
	@echo "Tether - AI Planning Orchestration System"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        Install dependencies"
	@echo "  make test           Run test suite"
	@echo "  make coverage       Run tests with coverage report"
	@echo "  make lint           Run code linters"
	@echo "  make format         Format code with black"
	@echo "  make clean          Clean build artifacts"
	@echo "  make run-examples   Run example demonstrations"

install:
	pip install -r requirements.txt
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest -v

coverage:
	pytest --cov=. --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	flake8 tether.py cli.py config/ integrations/
	mypy tether.py cli.py --ignore-missing-imports

format:
	black tether.py cli.py examples.py config/ integrations/ tests/

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf *.egg-info
	rm -rf build dist
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

run-examples:
	python examples.py

run-demo:
	python tether.py

validate-example:
	python cli.py validate examples/example_plan.json

health-check:
	python cli.py health
