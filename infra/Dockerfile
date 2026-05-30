# Multi-target Dockerfile for ConvIQ.
#
#   docker build --target api    -t conviq-api    -f infra/Dockerfile .
#   docker build --target worker -t conviq-worker -f infra/Dockerfile .
#
# The two targets share the builder + runtime-base layers so the disk + cache
# footprint is small.

# ===== Builder =====================================================
FROM python:3.12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip

COPY pyproject.toml README.md ./
COPY apps ./apps
COPY core ./core
COPY pipeline ./pipeline

# Install only runtime dependencies; dev/training/eval extras stay out of images.
RUN /opt/venv/bin/pip install --no-cache-dir .

# ===== Runtime base =================================================
FROM python:3.12-slim AS runtime-base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# ffmpeg is required by openai-whisper for audio decoding
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv

RUN useradd -m -u 1000 conviq

WORKDIR /app

COPY --chown=conviq:conviq apps ./apps
COPY --chown=conviq:conviq core ./core
COPY --chown=conviq:conviq pipeline ./pipeline
COPY --chown=conviq:conviq domains ./domains
COPY --chown=conviq:conviq alembic.ini ./alembic.ini
COPY --chown=conviq:conviq infra/alembic ./infra/alembic
COPY --chown=conviq:conviq infra/entrypoint-api.sh /usr/local/bin/entrypoint-api.sh

RUN chmod +x /usr/local/bin/entrypoint-api.sh

USER conviq

# ===== API target ===================================================
FROM runtime-base AS api

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint-api.sh"]


# ===== Worker target ================================================
FROM runtime-base AS worker

CMD ["celery", "-A", "apps.worker.celery_app:celery_app", "worker", \
     "--loglevel=info", "--concurrency=2"]
