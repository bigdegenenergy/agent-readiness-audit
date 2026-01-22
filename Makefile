.PHONY: help install lint format typecheck test test-cov check build clean scan

# Default target
help:
	@echo "Available targets:"
	@echo "  install    - Install dependencies with uv"
	@echo "  lint       - Run ruff linter"
	@echo "  format     - Run ruff formatter"
	@echo "  typecheck  - Run mypy type checker"
	@echo "  test       - Run pytest"
	@echo "  test-cov   - Run pytest with coverage"
	@echo "  check      - Run all quality checks (lint, format, typecheck, test)"
	@echo "  build      - Build the package"
	@echo "  clean      - Remove build artifacts"
	@echo "  scan       - Run ara self-audit"

install:
	uv sync

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy agent_readiness_audit

test:
	uv run pytest

test-cov:
	uv run pytest --cov=agent_readiness_audit

check: lint format-check typecheck test
	@echo "All checks passed!"

build:
	uv build

clean:
	rm -rf dist/ build/ *.egg-info/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

scan:
	uv run ara scan --repo .
