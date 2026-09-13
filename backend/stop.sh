#!/usr/bin/env bash
# Stop the Celery worker started by ./start.sh.
#
# Asks it to finish the audit it is running, then forces the issue if it will not go.
#   ./stop.sh
#   TIMEOUT=60 ./stop.sh
set -euo pipefail

cd "$(dirname "$0")"

PID_FILE=".celery/worker.pid"
TIMEOUT="${TIMEOUT:-30}"

if [ ! -f "$PID_FILE" ]; then
  echo "No pid file at $PID_FILE; nothing started by this script is running."
  exit 0
fi

pid="$(cat "$PID_FILE")"

if ! kill -0 "$pid" 2>/dev/null; then
  echo "Worker $pid is already gone. Clearing pid file."
  rm -f "$PID_FILE"
  exit 0
fi

# TERM is Celery's warm shutdown: it stops taking work and finishes the current audit,
# which leaves the job row written rather than stuck at "running".
echo "Stopping worker $pid (waiting up to ${TIMEOUT}s for the current audit to finish)…"
kill -TERM "$pid"

for _ in $(seq "$TIMEOUT"); do
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "Worker stopped."
    exit 0
  fi
  sleep 1
done

echo "Worker did not stop in ${TIMEOUT}s; forcing it." >&2
kill -KILL "$pid" 2>/dev/null || true
sleep 1
rm -f "$PID_FILE"
echo "Worker killed. Any audit it was mid-way through stays 'running' until rerun."
