.PHONY: help up down build restart logs logs-all test test-cov test-security lint format typecheck migrate-up migrate-down seed shell-backend shell-app-db shell-target-db shell-redis cache-clear clean dev frontend-install frontend-dev

# ── Help ──
help: ## Show available commands
	@echo ""
	@echo "QueryMate AI — Development Commands"
	@echo "===================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Docker ──
up: ## Start all services (PostgreSQL x2, Redis, backend, frontend)
	docker compose up -d
	@echo ""
	@echo "QueryMate AI is running:"
	@echo "  Frontend:   http://localhost:3000"
	@echo "  Backend:    http://localhost:8000"
	@echo "  API Docs:   http://localhost:8000/docs"
	@echo ""
	@echo "Demo database seeded with ~2,000 rows across 8 tables."
	@echo "Try: 'What are the top 5 best-selling products?'"

down: ## Stop all services
	docker compose down

build: ## Rebuild all containers (no cache)
	docker compose build --no-cache

restart: ## Restart all services
	docker compose restart

# ── Logs ──
logs: ## Tail backend logs
	docker compose logs -f backend

logs-all: ## Tail all service logs
	docker compose logs -f

# ── Testing ──
test: ## Run all tests
	docker compose exec backend pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	docker compose exec backend pytest tests/ --cov=backend --cov-report=term-missing

test-security: ## Run SQL validator security tests only
	docker compose exec backend pytest tests/unit/test_sql_validator.py -v

# ── Code Quality ──
lint: ## Run linter (ruff)
	ruff check backend/ tests/

format: ## Auto-format code (ruff)
	ruff format backend/ tests/

typecheck: ## Run type checker (mypy)
	mypy backend/

# ── Database ──
migrate-up: ## Run database migrations
	alembic upgrade head

migrate-down: ## Rollback last migration
	alembic downgrade -1

seed: ## Seed demo e-commerce data (~2,000 rows)
	docker compose exec target_db psql -U demo_user -d ecommerce_demo -f /docker-entrypoint-initdb.d/01_seed.sql

shell-app-db: ## Open psql shell to app database
	docker compose exec app_db psql -U querymate -d querymate_app

shell-target-db: ## Open psql shell to target (demo) database
	docker compose exec target_db psql -U demo_user -d ecommerce_demo

# ── Utilities ──
shell-backend: ## Open bash shell in backend container
	docker compose exec backend /bin/bash

shell-redis: ## Open Redis CLI
	docker compose exec redis redis-cli

cache-clear: ## Clear all Redis caches
	docker compose exec redis redis-cli FLUSHALL
	@echo "All Redis caches cleared."

# ── Local Development (without Docker) ──
dev: ## Start backend locally (requires venv)
	uvicorn backend.app.main:app --reload --port 8000

frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Start frontend dev server
	cd frontend && npm run dev

# ── Cleanup ──
clean: ## Remove all containers, volumes, and build artifacts
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache htmlcov .coverage
	@echo "Cleaned up all containers, volumes, and build artifacts."
