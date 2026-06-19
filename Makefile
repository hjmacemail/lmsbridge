# LMS Bridge developer convenience targets
.DEFAULT_GOAL := help
SHELL := /bin/bash

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ---- Local (no Docker) ----
backend-install: ## Create venv and install backend deps
	cd backend && python3 -m venv .venv && . .venv/bin/activate && \
	  pip install -U pip && pip install -e ".[dev]"

backend-run: ## Run the API with autoreload
	cd backend && . .venv/bin/activate && \
	  uvicorn app.main:app --reload --port $${API_PORT:-8000}

backend-seed: ## Seed the database with demo course/student data
	cd backend && . .venv/bin/activate && python -m app.scripts.seed

backend-test: ## Run backend test suite
	cd backend && . .venv/bin/activate && pytest -q

backend-lint: ## Lint + type-check backend
	cd backend && . .venv/bin/activate && ruff check app tests && mypy app

migrate: ## Apply database migrations
	cd backend && . .venv/bin/activate && alembic upgrade head

frontend-install: ## Install frontend deps
	cd frontend && npm install

frontend-run: ## Run the frontend dev server
	cd frontend && npm run dev

frontend-build: ## Production build of the frontend
	cd frontend && npm run build

# ---- Docker ----
up: ## Build and start the full stack (docker compose)
	docker compose up --build

down: ## Stop the stack
	docker compose down

logs: ## Tail stack logs
	docker compose logs -f

.PHONY: help backend-install backend-run backend-seed backend-test backend-lint migrate frontend-install frontend-run frontend-build up down logs
