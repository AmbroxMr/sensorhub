default:
    @just --list

# ── Dev ────────────────────────────────────────────────────────────────────────

dev:
    uv run uvicorn sensorhub.api:app --reload --port 8000

frontend:
    uv run --group frontend streamlit run frontend/app.py

# ── Tests ──────────────────────────────────────────────────────────────────────

test:
    uv run pytest tests/unit/ -v

test-integration:
    uv run pytest tests/integration/ -v

test-cov:
    uv run pytest tests/unit/ -v --cov=sensorhub --cov-report=term-missing

# ── Lint & format ──────────────────────────────────────────────────────────────

lint:
    uv run ruff check .

lint-fix:
    uv run ruff check . --fix

format:
    uv run ruff format .

format-check:
    uv run ruff format . --check

typecheck:
    uv run ty check sensorhub/

check: lint format-check typecheck test

# ── Version ────────────────────────────────────────────────────────────────────

bump-patch:
    uv version --bump patch

bump-minor:
    uv version --bump minor

bump-major:
    uv version --bump major

# ── Docker ─────────────────────────────────────────────────────────────────────

up:
    docker compose up -d

down:
    docker compose down

logs:
    docker compose logs -f api

build:
    docker compose build
