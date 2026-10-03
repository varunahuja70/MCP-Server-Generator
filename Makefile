.PHONY: help dev test test-backend test-frontend lint lint-backend lint-frontend migrate seed build

help:
	@echo "MCP Forge Development Commands:"
	@echo "  make dev           Run backend and frontend concurrently with reload"
	@echo "  make test          Run all backend and frontend tests"
	@echo "  make lint          Run all linting and typechecking"
	@echo "  make migrate       Run database migrations"
	@echo "  make seed          Seed sample specifications"
	@echo "  make build         Build backend package and frontend assets"

dev:
	@echo "Starting backend and frontend..."
	sh -c "(cd backend && uv run uvicorn mcp_forge.api.app:create_app --factory --reload --port 8080) & (cd frontend && pnpm dev)"

test: test-backend test-frontend

test-backend:
	cd backend && uv run pytest

test-frontend:
	cd frontend && pnpm test

lint: lint-backend lint-frontend

lint-backend:
	cd backend && uv run ruff check .
	cd backend && uv run ruff format --check .
	cd backend && uv run mypy src tests

lint-frontend:
	cd frontend && pnpm lint
	cd frontend && pnpm tsc --noEmit

migrate:
	cd backend && uv run alembic upgrade head

seed:
	cd backend && uv run python -m mcp_forge.cli.main samples --seed

build:
	cd backend && uv build
	cd frontend && pnpm build
