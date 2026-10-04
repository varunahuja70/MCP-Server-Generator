# Production Dockerfile for MCP Forge Backend
FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Install runtime dependencies and CA certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install pinned uv binary
COPY --from=ghcr.io/astral-sh/uv:0.5.15 /uv /bin/uv

# Copy project definition and lockfile for caching
COPY backend/pyproject.toml backend/uv.lock ./

# Sync dependencies using frozen lockfile without dev tools
RUN uv sync --frozen --no-dev --no-install-project

# Copy backend source
COPY backend/src ./src

# Create non-root user and data volume mount
RUN useradd -u 10001 -m -s /bin/bash appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://127.0.0.1:8080/healthz || exit 1

ENTRYPOINT ["uv", "run", "uvicorn", "mcp_forge.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
