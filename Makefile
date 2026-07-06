# Delhi Metro Digital Twin — operational Makefile
# Requires: docker, docker compose, node, python3.12
# Usage:  make <target>     (run `make help` for a list)

COMPOSE := docker compose -f docker/docker-compose.yml --env-file configs/dev.env
PY      := python3.12
PIP     := $(PY) -m pip

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@echo "Delhi Metro Digital Twin"
	@echo "========================="
	@echo ""
	@echo "Targets:"
	@awk '/^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$$$(NF) }' $(MAKEFILE_LIST) | sed 's/##//g'

# ──────────────── Stack lifecycle ────────────────
.PHONY: up down restart ps logs
up: ## Build and start the full stack
	$(COMPOSE) up --build -d
	@echo "Frontend → http://localhost:3000"
	@echo "API      → http://localhost:8000/docs"

up-attach: ## Start stack in foreground
	$(COMPOSE) up --build

down: ## Stop the full stack
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

ps: ## Show running services
	$(COMPOSE) ps

logs: ## Tail logs (all services)
	$(COMPOSE) logs -f --tail=200

logs-svc: ## Tail a single service: make logs-svc SVC=backend
	$(COMPOSE) logs -f --tail=200 $(SVC)

# ──────────────── Database ────────────────
.PHONY: migrate migrate-new seed psql dbshell
migrate: ## Apply all pending migrations
	$(COMPOSE) exec -T backend alembic upgrade head

migrate-new: ## Create a migration: make migrate-new MSG="add foo"
	$(COMPOSE) exec -T backend alembic revision --autogenerate -m "$(MSG)"

seed: ## Seed the network + timetables
	$(COMPOSE) exec -T backend python scripts/seed_network.py

psql: ## Open a psql shell on the database
	$(COMPOSE) exec -T postgres psql -U "$${POSTGRES_USER:-dmdt}" -d "$${POSTGRES_DB:-dmdt}"

dbshell: psql

# ──────────────── Backend ────────────────
.PHONY: backend-shell backend-test backend-lint backend-fmt
backend-shell: ## Shell into backend container
	$(COMPOSE) exec backend bash

backend-test: ## Run pytest inside backend
	$(COMPOSE) exec -T backend pytest -q

backend-lint:
	$(COMPOSE) exec -T backend ruff check app

backend-fmt:
	$(COMPOSE) exec -T backend ruff format app

# ──────────────── Simulation ────────────────
.PHONY: sim-run sim-test
sim-run: ## Run the simulation headless for 24 simulated hours
	$(COMPOSE) exec -T simulation python -m dmdt_sim.cli run --hours 24

sim-test: ## Run simulation unit tests
	$(COMPOSE) exec -T simulation pytest -q

# ──────────────── Frontend ────────────────
.PHONY: fe fe-install fe-test fe-build fe-lint
fe: ## Run frontend in dev (host)
	cd frontend && npm run dev

fe-install:
	cd frontend && npm install

fe-test:
	cd frontend && npm test -- --run

fe-build:
	cd frontend && npm run build

fe-lint:
	cd frontend && npm run lint

# ──────────────── Dev (host-mounted) ────────────────
.PHONY: venv fe-venv
venv: ## Create the python simulation/backend venv on the host
	$(PY) -m venv .venv
	. .venv/bin/activate && $(PIP) install --upgrade pip wheel setuptools

fe-venv:
	cd frontend && npm install
