#!/usr/bin/env bash
# Start the Celery worker that generates audits.
#
# Detached by default so the shell stays usable; pass --foreground to watch it live.
#   ./start.sh
#   ./start.sh --foreground
#   LOGLEVEL=debug CONCURRENCY=4 ./start.sh
set -euo pipefail

cd "$(dirname "$0")"

RUN_DIR=".celery"
PID_FILE="$RUN_DIR/worker.pid"
LOG_FILE="$RUN_DIR/worker.log"
LOGLEVEL="${LOGLEVEL:-info}"
CONCURRENCY="${CONCURRENCY:-2}"
FOREGROUND=0

for arg in "$@"; do
  case "$arg" in
    --foreground|-f) FOREGROUND=1 ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

mkdir -p "$RUN_DIR"

# A worker already running would double-consume the queue, so refuse rather than add one.
if [ -f "$PID_FILE" ]; then
  existing="$(cat "$PID_FILE")"
  if kill -0 "$existing" 2>/dev/null; then
    echo "Worker already running (pid $existing). Stop it first: ./stop.sh"
    exit 1
  fi
  echo "Clearing stale pid file for $existing."
  rm -f "$PID_FILE"
fi

# Read REDIS_URL the same way the app does, so the check matches what Celery will use.
REDIS_URL="$(uv run python -c 'from app.core.config import get_settings; print(get_settings().redis_url)')"

if ! uv run python - "$REDIS_URL" <<'PY'
import sys
from urllib.parse import urlparse

import redis

url = urlparse(sys.argv[1])
try:
    redis.Redis(host=url.hostname or "localhost", port=url.port or 6379, socket_connect_timeout=3).ping()
except Exception as error:  # noqa: BLE001 - any failure means the broker is unusable
    print(f"  {type(error).__name__}: {error}", file=sys.stderr)
    raise SystemExit(1)
PY
then
  echo "Cannot reach Redis at $REDIS_URL." >&2
  echo "Start it with 'brew services start redis', or set REDIS_URL to another broker." >&2
  echo "To run audits without a worker instead, set CELERY_ALWAYS_EAGER=true." >&2
  exit 1
fi

echo "Broker: $REDIS_URL"

if [ "$FOREGROUND" -eq 1 ]; then
  echo "Starting worker in the foreground. Press Ctrl-C to stop."
  exec uv run celery -A app.worker worker --loglevel="$LOGLEVEL" --concurrency="$CONCURRENCY"
fi

uv run celery -A app.worker worker --loglevel="$LOGLEVEL" --concurrency="$CONCURRENCY" \
  >>"$LOG_FILE" 2>&1 &
pid=$!
echo "$pid" > "$PID_FILE"

# Celery exits early on a bad broker or import error; make sure it is still up.
sleep 2
if ! kill -0 "$pid" 2>/dev/null; then
  rm -f "$PID_FILE"
  echo "Worker exited immediately. Last lines of $LOG_FILE:" >&2
  tail -n 20 "$LOG_FILE" >&2
  exit 1
fi

echo "Worker started (pid $pid), concurrency $CONCURRENCY, logging to $LOG_FILE"
echo "Stop it with ./stop.sh"
