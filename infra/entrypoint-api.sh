#!/usr/bin/env bash
# API container entrypoint: apply migrations, then launch gunicorn.
set -euo pipefail

echo "[entrypoint] Running database migrations…"
alembic upgrade head

echo "[entrypoint] Starting gunicorn…"
exec gunicorn apps.api.main:app \
    --bind 0.0.0.0:8000 \
    --worker-class uvicorn.workers.UvicornWorker \
    --workers "${API_WORKERS:-2}" \
    --timeout "${API_TIMEOUT:-300}" \
    --access-logfile - \
    --error-logfile -
