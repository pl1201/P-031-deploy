.PHONY: test lint validate-data graph check
test:
	python3 -m pytest -q
validate-data:
	python3 scripts/validate_data.py
graph:
	python3 -c "import sys;sys.path.insert(0,'.');from scripts.render_graph import main;main()"
check: validate-data test
