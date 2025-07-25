###############################################################################
# Multi-stage Docker build for Python FastAPI application using Poetry
###############################################################################

# ─── BUILD ARGUMENTS ─────────────────────────────────────────────────────────
ARG PYTHON_VERSION=3.10
ARG PYTHON_VARIANT=slim

FROM python:${PYTHON_VERSION}-${PYTHON_VARIANT}

# ─── STAGE-LEVEL BUILD ARGS ───────────────────────────────────────────────────
ARG POETRY_VERSION=1.8.3
ARG APP_PORT=8000
ARG HEALTH_CHECK_PORT=8000
ARG APP_USER=app
ARG APP_GROUP=app
ARG WORKDIR=/app

# ─── METADATA ─────────────────────────────────────────────────────────────────
LABEL maintainer="ScholarAI Team"
LABEL description="ScholarAI Backend API Service"
LABEL version="1.0.0"

# ─── ENVIRONMENT ──────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/opt/poetry \
    POETRY_VERSION=${POETRY_VERSION} \
    APP_PORT=${APP_PORT} \
    APP_USER=${APP_USER} \
    APP_GROUP=${APP_GROUP} \
    PYTHONPATH=/app

# ─── SYSTEM DEPENDENCIES ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/* \
  && apt-get clean

# ─── INSTALL POETRY ────────────────────────────────────────────────────────────
RUN pip install --no-cache-dir poetry==${POETRY_VERSION}
RUN poetry config virtualenvs.create false

# ─── WORKDIR ──────────────────────────────────────────────────────────────────
WORKDIR ${WORKDIR}

# ─── COPY PROJECT FILES ─────────────────────────────────────────────────────────
COPY pyproject.toml poetry.lock ./

# ─── INSTALL DEPENDENCIES ONLY ─────────────────────────────────────────────────────
RUN poetry install --only=main --no-dev --no-root

# ─── COPY APP CODE ─────────────────────────────────────────────────────────────
COPY app/ ./app/

# ─── SECURITY & USER ──────────────────────────────────────────────────────────
RUN groupadd --system ${APP_GROUP} \
  && useradd --system --gid ${APP_GROUP} --create-home --shell /bin/bash ${APP_USER} \
  && chown -R ${APP_USER}:${APP_GROUP} ${WORKDIR}
USER ${APP_USER}

# ─── NETWORK & HEALTHCHECK ────────────────────────────────────────────────────
EXPOSE ${APP_PORT}
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${HEALTH_CHECK_PORT}/health || exit 1

# ─── CMD ──────────────────────────────────────────────────────────────────────
CMD ["sh", "-c", "cd /app && python -m uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT}"]
