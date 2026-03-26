PYTHON ?= python3

.PHONY: setup lint test demo

setup:
	$(PYTHON) -m ensurepip --upgrade >/dev/null 2>&1 || true
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	ruff check src tests

test:
	pytest -q

demo:
	$(PYTHON) -m postmortem_shield demo --input samples/postmortems/payment-api-latency.md --output samples/generated
