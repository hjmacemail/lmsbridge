# ---- LMS Bridge backend image ----
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System deps for psycopg + healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl libpq-dev && rm -rf /var/lib/apt/lists/*

# Install dependencies first (better layer caching)
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
RUN pip install -U pip && pip install -e .

# Run as non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=5 \
  CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

CMD ["sh", "-c", "alembic upgrade head && python -m app.scripts.seed --if-empty && uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT:-8000}"]
