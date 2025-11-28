.PHONY: setup hooks

setup:
	uv pip install -e ".[dev,test]"

hooks:
	pre-commit install
	pre-commit install --hook-type pre-push
