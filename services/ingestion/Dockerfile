FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/app/.venv UV_COMPILE_BYTECODE=1
WORKDIR /app

# uv needs every workspace manifest to resolve the graph, so copy all of
# src/services manifests even though this image only installs one package.
COPY pyproject.toml uv.lock .python-version README.md ./
COPY src ./src
COPY services ./services
RUN uv sync --frozen --package f1-ingestion-service --no-dev --no-editable

FROM python:3.12-slim
WORKDIR /app
COPY --from=base /app/.venv /app/.venv
COPY src ./src
COPY services/ingestion ./services/ingestion
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "f1_ingestion_service.main"]
