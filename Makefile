.PHONY: setup install dev hooks test lint typecheck format pre-commit

# System prerequisites (run once per machine)
setup:
	@command -v uv >/dev/null || (echo "Installing uv..." && brew install uv)
	@command -v python3.12 >/dev/null || (echo "Installing Python 3.12..." && brew install python@3.12)

# Project dependencies (run after clone)
install: setup
	uv sync --extra dev --extra test

# Dev environment (install + hooks)
dev: install hooks

# Git hooks
hooks:
	uv run pre-commit install
	uv run pre-commit install --hook-type pre-push

# Run tests
test:
	uv run pytest

# Run linter
lint:
	uv run ruff check .

# Run type checker
typecheck:
	uv run python -m mypy src/

# Format code
format:
	uv run ruff format .

# Run full pre-commit suite
pre-commit:
	uv run pre-commit run --all-files
