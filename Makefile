.PHONY: install install-dev test lint clean run version generate sample info compare compare-methods assets pages streamlit ci typecheck

install:
	python3 -m pip install -e .

install-dev:
	python3 -m pip install -e ".[dev]"

install-all:
	python3 -m pip install -e ".[all]"

test:
	python3 -m pytest tests/ -v

lint:
	python3 -m ruff check src/ tests/

typecheck:
	python3 -m mypy src/teselado

ci: lint typecheck test

sample:
	python3 -m teselado generate --city demo --restaurants 50 --orders 500 --seed 42 --output data/sample

generate:
	python3 -m teselado generate

info:
	python3 -m teselado info --data-dir data/sample

run:
	python3 -m teselado run

compare:
	python3 -m teselado compare

compare-methods:
	python3 -m teselado compare-methods --k 5

assets:
	python3 scripts/generate_portfolio_assets.py

pages: assets

streamlit:
	streamlit run streamlit_app.py

viz:
	python3 -m teselado viz

version:
	python3 -m teselado version

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
