PACKAGE = src

.DEFAULT_GOAL := help

help:
	@echo "Commands:"
	@echo "  install      Install dependencies (uv sync)"
	@echo "  run          Run the program"
	@echo "  debug        Run with pdb"
	@echo "  clean        Remove cache files"
	@echo "  lint         Run flake8 and mypy"
	@echo "  lint-strict  Run flake8 and mypy --strict"

install:
	uv sync

run:
	uv run python -m $(PACKAGE)

debug:
	uv run python -m pdb -m $(PACKAGE)

clean:
	@echo "Cleaning cache files..."
	@find . -type d -name .venv -prune -o -type d -name __pycache__ -exec rm -rf {} +
	@find . -type d -name .venv -prune -o -type d -name .mypy_cache -exec rm -rf {} +
	@echo "Clean complete"

lint:
	uv run flake8 . --exclude=llm_sdk,.venv
	uv run mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs --exclude=llm_sdk

lint-strict:
	uv run flake8 . --exclude=llm_sdk,.venv
	uv run mypy . --strict --exclude=llm_sdk

.PHONY: help install run debug clean lint lint-strict
