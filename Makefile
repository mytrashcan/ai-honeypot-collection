COMPOSE ?= docker compose
PYTHON ?= python3
RUFF ?= ruff

.PHONY: up down build logs test test-fastapi clean lint status

up:
	$(COMPOSE) up --detach --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

logs:
	$(COMPOSE) logs --follow

test:
	$(PYTHON) -m unittest discover -s tests -v

test-fastapi:
	$(PYTHON) -m pip install --requirement requirements-dev.txt
	$(PYTHON) -m unittest discover -s tests -v

clean:
	find honeypot_common categories tests -type d -name __pycache__ -prune -exec rm -rf {} +
	find honeypot_common categories tests -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
	rm -rf build dist .pytest_cache .ruff_cache
	find . -maxdepth 1 -type d -name '*.egg-info' -exec rm -rf {} +

lint:
	$(RUFF) check .

status:
	$(COMPOSE) ps
