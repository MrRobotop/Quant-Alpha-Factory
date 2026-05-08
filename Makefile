PYTHON ?= .venv/bin/python
IMAGE ?= quant-alpha-factory:local

.PHONY: install install-real lint format test smoke ci doctor doctor-no-llm quickstart validate-release qlib-demo-dry qlib-demo-real docker-build docker-test clean

.venv/bin/python:
	python3 -m venv .venv

install: .venv/bin/python
	$(PYTHON) -m pip install -e ".[dev]"

install-real: .venv/bin/python
	$(PYTHON) -m pip install -e ".[dev,api,dashboard,qlib,rdagent]"

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

test:
	$(PYTHON) -m pytest

smoke:
	$(PYTHON) -m pytest tests/test_smoke.py

ci: lint test

doctor:
	$(PYTHON) -m src.cli doctor --component all --strict

doctor-no-llm:
	$(PYTHON) -m src.cli doctor --component all --allow-missing-llm --skip-docker-daemon

quickstart: ci
	$(PYTHON) -m src.cli status
	$(PYTHON) -m src.cli data validate --input data/sample/prices.csv
	$(PYTHON) -m src.cli research check --config configs/qlib/baseline_lightgbm_alpha158.yaml
	$(PYTHON) -m src.cli qlib demo --dry-run
	$(PYTHON) -m src.cli rdagent health --dry-run
	$(PYTHON) -m src.cli rdagent run --mode fin_factor --loop-n 1 --dry-run
	$(PYTHON) -m src.cli demo synthetic

validate-release: quickstart doctor-no-llm

qlib-demo-dry:
	$(PYTHON) -m src.cli qlib demo --dry-run

qlib-demo-real:
	$(PYTHON) -m src.cli doctor --component qlib --strict
	$(PYTHON) -m src.cli qlib demo --execute

docker-build:
	docker build -t $(IMAGE) .

docker-test:
	docker run --rm $(IMAGE) python -m pytest

clean:
	rm -rf .pytest_cache .ruff_cache
	rm -rf api/__pycache__ dashboard/__pycache__ src/__pycache__ tests/__pycache__
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -prune -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -prune -exec rm -rf {} +
