FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy agent_core wheel and project files
COPY agent_core-*.whl ./
COPY pyproject.toml uv.lock ./

# Sync dependencies (skip agent-core from editable path), then install wheel
RUN uv sync --frozen --no-install-package agent-core && \
    uv pip install agent_core-*.whl && \
    rm agent_core-*.whl

COPY . .

ENV CONFIG_FILE=/app/config.yaml


EXPOSE 8000

CMD ["uv", "run", "--no-sync", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

