.PHONY: start django api install migrate test help

# ── Default target ────────────────────────────────────────────────────────────
help:
	@echo "Usage:"
	@echo "  make start     — Start Django (port 8000) and FastAPI (port 8001)"
	@echo "  make django    — Start Django server only"
	@echo "  make api       — Start FastAPI server only"
	@echo "  make install   — Install all dependencies"
	@echo "  make migrate   — Apply database migrations"
	@echo "  make test      — Run the full test suite"

# ── Start both servers ────────────────────────────────────────────────────────
start:
	@echo "Starting Django on http://localhost:8000 and FastAPI on http://localhost:8001"
	@trap 'kill 0' INT; \
	uv run python manage.py runserver 8000 & \
	uv run uvicorn api.main:app --reload --port 8001 & \
	wait

# ── Individual servers ────────────────────────────────────────────────────────
django:
	uv run python manage.py runserver 8000

api:
	uv run uvicorn api.main:app --reload --port 8001

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	uv sync

migrate:
	uv run python manage.py migrate

# ── Tests ─────────────────────────────────────────────────────────────────────
test:
	uv run pytest
