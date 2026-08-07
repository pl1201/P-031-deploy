.PHONY: run test test-fast test-clinical test-agents test-api test-db lint format format-check type-check validate-data structure graph check seed seed-demo-users eval
run:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
test:
	python3 -m pytest -q
test-fast:
	python3 -m pytest -q -m "not slow"
# Chạy test theo từng nhóm — dùng khi chỉ sửa một phần, tránh quét toàn bộ suite.
test-clinical:
	python3 -m pytest -q tests/test_clinical.py tests/test_menu_generator.py tests/test_dishes.py tests/test_food_item.py
test-agents:
	python3 -m pytest -q tests/test_agent.py tests/test_assembly_generator_choice.py tests/test_graph_e2e.py tests/test_guardrail.py tests/test_hybrid_generator.py tests/test_cpsat_optimizer.py
test-api:
	python3 -m pytest -q tests/test_api_auth.py tests/test_api_meal_plans.py tests/test_api_patients.py tests/test_api_reviews.py tests/test_api_targets.py
test-db:
	python3 -m pytest -q tests/test_db_models.py tests/test_seed_db.py tests/test_seed_demo_users.py
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
