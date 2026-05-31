#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CONDA_BIN="${CONDA_BIN:-/home/k0de/miniforge3/bin/conda}"
ENV_DIR="${ENV_DIR:-/home/k0de/miniforge3/envs/ai}"
PYTHON_BIN="${PYTHON_BIN:-$ENV_DIR/bin/python}"
UVICORN_BIN="${UVICORN_BIN:-$ENV_DIR/bin/uvicorn}"
CELERY_BIN="${CELERY_BIN:-$ENV_DIR/bin/celery}"
API_HOST="${API_HOST:-0.0.0.0}"
API_PORT="${API_PORT:-8000}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
OPEN_BROWSER="${OPEN_BROWSER:-1}"

PIDS=()
CLEANED_UP=0

cleanup() {
  if [[ "$CLEANED_UP" == "1" ]]; then
    return
  fi
  CLEANED_UP=1
  set +e
  echo
  echo "Stopping ConvIQ local dev services..."
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" 2>/dev/null
  done
  wait "${PIDS[@]:-}" 2>/dev/null
  docker compose -f infra/docker-compose.yml down
}

trap cleanup EXIT INT TERM

require_file() {
  if [[ ! -x "$1" ]]; then
    echo "Missing executable: $1" >&2
    exit 1
  fi
}

require_file "$CONDA_BIN"
require_file "$PYTHON_BIN"
require_file "$UVICORN_BIN"
require_file "$CELERY_BIN"

FRONTEND_PORT="$(
  "$PYTHON_BIN" -c '
import socket
import sys

host = sys.argv[1]
start = int(sys.argv[2])

for port in range(start, start + 100):
    with socket.socket() as sock:
        try:
            sock.bind((host, port))
        except OSError:
            continue
        print(port)
        break
else:
    raise SystemExit(f"No free frontend port found from {start} to {start + 99}")
' "$FRONTEND_HOST" "$FRONTEND_PORT"
)"

echo "Starting Postgres and Redis..."
docker compose -f infra/docker-compose.yml up -d postgres redis

echo "Running migrations..."
PYTHONPATH=. "$CONDA_BIN" run -n ai alembic upgrade head

echo "Starting API on http://localhost:$API_PORT ..."
PYTHONPATH=. "$UVICORN_BIN" apps.api.main:app \
  --host "$API_HOST" \
  --port "$API_PORT" \
  --log-level info &
PIDS+=("$!")

echo "Starting Celery worker..."
PYTHONPATH=. "$CELERY_BIN" -A apps.worker.celery_app:celery_app worker \
  --loglevel=info \
  --concurrency=1 &
PIDS+=("$!")

echo "Starting frontend on http://$FRONTEND_HOST:$FRONTEND_PORT ..."
"$PYTHON_BIN" -m http.server "$FRONTEND_PORT" \
  --bind "$FRONTEND_HOST" \
  --directory frontend &
PIDS+=("$!")

sleep 1
for pid in "${PIDS[@]}"; do
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "A local dev process exited during startup. Check the logs above." >&2
    exit 1
  fi
done

echo
echo "ConvIQ local dev is running."
echo "Frontend: http://$FRONTEND_HOST:$FRONTEND_PORT"
echo "API docs: http://localhost:$API_PORT/docs"
echo "Press Ctrl+C to stop everything."

if [[ "$OPEN_BROWSER" == "1" ]] && command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://$FRONTEND_HOST:$FRONTEND_PORT" >/dev/null 2>&1 || true
fi

wait -n "${PIDS[@]}"
