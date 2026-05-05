.PHONY: up down build test-backend test-frontend test lint

up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

test-backend:
	cd backend && pytest --cov=app --cov-report=html --cov-fail-under=95 -v

test-frontend:
	cd frontend && npm run test -- --coverage

test: test-backend test-frontend

lint:
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run lint
