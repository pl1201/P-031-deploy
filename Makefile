.PHONY: run test test-fast lint format format-check type-check validate-data structure graph check seed seed-demo-users eval
run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
test:
	python3 -m pytest -q
test-fast:
	python3 -m pytest -q -m "not slow"
lint:
	python3 -m ruff check src/ tests/
format:
	python3 -m ruff format src/ tests/ scripts/ eval/
format-check:
	python3 -m ruff format --check src/ tests/ scripts/ eval/
type-check:
	python3 -m mypy src/
validate-data:
	python3 scripts/validate_data.py
structure:
	python3 scripts/check_structure.py
seed:
	python3 scripts/seed_db.py
seed-demo-users:
	python3 scripts/seed_demo_users.py
graph:
	python3 -c "import sys;sys.path.insert(0,'.');from scripts.render_graph import main;main()"
eval:
	@echo "Evaluation runner not yet implemented (EVL-02)"
	@exit 1
check: lint format-check type-check structure validate-data test
