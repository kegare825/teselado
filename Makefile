.PHONY: install install-dev test lint clean run version

install:
	python3 -m pip install -e .

install-dev:
	python3 -m pip install -e ".[dev]"

test:
	python3 -m pytest tests/ -v

lint:
	python3 -m ruff check src/ tests/

run:
	python3 -m teselado run

version:
	python3 -m teselado version

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
