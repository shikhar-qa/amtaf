INTENT ?= Set the syslog server to 10.0.0.5 in the management UI and verify it was applied on the device within 10 seconds.
FAULT_URL = http://localhost:8080/api/fault

.PHONY: install test lint up down generate demo demo-fault

install:
	pip install -e ".[dev,gui,llm]"
	playwright install chromium

test:
	pytest

lint:
	black --check amtaf tests demo
	flake8 amtaf tests demo
	mypy amtaf

up:
	docker compose up -d --build

down:
	docker compose down

generate:
	python -m amtaf.cli generate "$(INTENT)"

# Happy path: GUI change is applied on the device
demo: up generate
	pytest generated -v --alluredir=allure-results

# Fault path: UI says Saved, device never persists; triage explains why
demo-fault: up generate
	curl -s -X POST $(FAULT_URL) -H 'content-type: application/json' -d '{"enabled": true}'
	-pytest generated -v --alluredir=allure-results
	curl -s -X POST $(FAULT_URL) -H 'content-type: application/json' -d '{"enabled": false}'
