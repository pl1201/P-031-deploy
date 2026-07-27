.PHONY: run test lint format validate-data graph check
run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
test:
	python3 -m pytest -q
lint:
	python3 -m ruff check src/ tests/
format:
	python3 -m ruff format src/ tests/ scripts/
validate-data:
	python3 scripts/validate_data.py
graph:
	python3 -c "import sys;sys.path.insert(0,'.');from scripts.render_graph import main;main()"
check: lint validate-data test
