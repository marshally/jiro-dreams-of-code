.PHONY: setup hooks

setup:
	uv venv --python 3.12
	uv pip install -e ".[dev,test]"

hooks:
	uv run pre-commit install
	uv run pre-commit install --hook-type pre-push
