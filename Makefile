.PHONY: install test lint api worker ingestion replay dev compose-up compose-down logs temporal-ui temporal-setup search-demo

export PATH := $(HOME)/.local/bin:$(PATH)

install:
	uv sync --frozen --all-packages --group dev

test:
	uv run pytest

lint:
	uv run ruff check scripts src services tests

api:
	uv run uvicorn f1_api.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	uv run python -m f1_worker.main

ingestion:
	uv run python -m f1_ingestion_service.main

replay:
	uv run python -m f1_replay.cli --session-key "$(SESSION_KEY)" $(if $(TELEMETRY_DRIVER),--telemetry-driver "$(TELEMETRY_DRIVER)")

plot:
	uv run python scripts/plot_session.py --session-key "$(SESSION_KEY)" --pair "$(PAIR)"

temporal-setup:
	docker exec f1-live-intelligence-temporal-1 \
		temporal operator search-attribute create --address temporal:7233 \
			--name SessionId --type Keyword \
			--name DriverPair --type Keyword \
			--name ModelVersion --type Keyword \
			--name SnapshotVersion --type Keyword

search-demo:
	uv run python scripts/temporal_search_demo.py

compose-up:
	docker compose up --build

dev:
	@test -f .env || cp .env.example .env
	docker compose up --build

compose-down:
	docker compose down -v

logs:
	docker compose logs -f

temporal-ui:
	open http://localhost:8080 || xdg-open http://localhost:8080 || true

ui:
	open http://localhost:8000/ui || xdg-open http://localhost:8000/ui || true
