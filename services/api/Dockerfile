FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT=/app/.venv UV_COMPILE_BYTECODE=1
WORKDIR /app

# uv needs every workspace manifest to resolve the graph, so copy all of
# src/services manifests even though this image only installs one package.
COPY pyproject.toml uv.lock .python-version README.md ./
COPY src ./src
COPY services ./services
RUN uv sync --frozen --package f1-api --no-dev --no-editable

FROM python:3.12-slim
WORKDIR /app
COPY --from=base /app/.venv /app/.venv
COPY src ./src
COPY services/api ./services/api
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "f1_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
