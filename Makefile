.PHONY: up down build up-prod logs test migrate seed shell-backend shell-db lint format help

# Default target
help:
	@echo "CortexOS — Available commands:"
	@echo ""
	@echo "  Development:"
	@echo "    make up              Start all services (dev mode)"
	@echo "    make down            Stop all services"
	@echo "    make build           Rebuild all images"
	@echo "    make logs            Tail all service logs"
	@echo "    make logs-backend    Tail backend logs only"
	@echo ""
	@echo "  Production:"
	@echo "    make up-prod         Start all services (production mode)"
	@echo "    make down-prod       Stop production services"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate         Run Alembic migrations (head)"
	@echo "    make migrate-down    Roll back one migration"
	@echo "    make seed            Seed database with default data"
	@echo "    make shell-db        Open psql shell"
	@echo ""
	@echo "  Testing & Quality:"
	@echo "    make test            Run full test suite with coverage"
	@echo "    make test-fast       Run tests without coverage (faster)"
	@echo "    make lint            Run ruff + mypy"
	@echo "    make format          Format code with ruff"
	@echo ""
	@echo "  Shells:"
	@echo "    make shell-backend   bash into backend container"
	@echo "    make shell-db        psql into postgres"
	@echo ""
	@echo "  Ops:"
	@echo "    make backup          Dump postgres to backups/"
	@echo "    make clean           Remove all containers + volumes (DESTRUCTIVE)"

# ─── Development ────────────────────────────────────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

restart:
	docker compose restart

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

logs-celery:
	docker compose logs -f celery

# ─── Production ─────────────────────────────────────────────────────────────

up-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

down-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml down

build-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# ─── Database ───────────────────────────────────────────────────────────────

migrate:
	docker compose exec backend alembic upgrade head

migrate-down:
	docker compose exec backend alembic downgrade -1

migrate-history:
	docker compose exec backend alembic history

seed:
	docker compose exec backend python -m app.scripts.seed

shell-db:
	docker compose exec postgres psql -U cortexos cortexos

# ─── Testing & Quality ──────────────────────────────────────────────────────

test:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=80

test-fast:
	docker compose exec backend pytest tests/ -v -x

test-ci:
	docker compose exec backend pytest tests/ -v --cov=app --cov-report=xml --cov-fail-under=80

lint:
	docker compose exec backend ruff check app/
	docker compose exec backend mypy app/ --ignore-missing-imports

format:
	docker compose exec backend ruff format app/
	docker compose exec backend ruff check --fix app/

# ─── Shells ─────────────────────────────────────────────────────────────────

shell-backend:
	docker compose exec backend bash

shell-celery:
	docker compose exec celery bash

# ─── Ops ────────────────────────────────────────────────────────────────────

backup:
	@mkdir -p backups
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S) && \
	docker compose exec -T postgres pg_dump -U cortexos cortexos > backups/cortexos_$$TIMESTAMP.sql && \
	echo "Backup saved: backups/cortexos_$$TIMESTAMP.sql"

clean:
	@echo "WARNING: This will delete ALL containers and volumes. Press Ctrl+C to abort."
	@sleep 5
	docker compose down -v --remove-orphans

# ─── Setup ──────────────────────────────────────────────────────────────────

setup:
	@bash scripts/setup.sh
