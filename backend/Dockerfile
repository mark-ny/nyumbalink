# ─────────────────────────────────────────────
#  NyumbaLink Backend — Multi-stage Dockerfile
# ─────────────────────────────────────────────

# ── Base ──────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc curl \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencies ──────────────────────────────
FROM base AS dependencies

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ── Development ───────────────────────────────
FROM dependencies AS development

RUN pip install watchdog pytest pytest-cov coverage

COPY . .

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]

# ── Production ────────────────────────────────
FROM dependencies AS production

# Non-root user
RUN addgroup --system nyumba && adduser --system --ingroup nyumba nyumba

COPY . .

# Create log directory
RUN mkdir -p /app/logs && chown -R nyumba:nyumba /app

USER nyumba

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Gunicorn — 4 workers, gevent async
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--worker-class", "sync", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "/app/logs/access.log", \
     "--error-logfile", "/app/logs/error.log", \
     "--log-level", "info", \
     "app:app"]
