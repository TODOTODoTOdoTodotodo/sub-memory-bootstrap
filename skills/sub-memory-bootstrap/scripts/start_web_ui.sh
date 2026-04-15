#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
HOST="${SUB_MEMORY_WEB_HOST:-127.0.0.1}"
PORT="${SUB_MEMORY_WEB_PORT:-8765}"
WEB_BIN="$PROJECT_DIR/.venv/bin/sub-memory-web"
BASE_DIR="${SUB_MEMORY_BASE_DIR:-$PROJECT_DIR/.codex/sub-memory}"

if [[ ! -x "$WEB_BIN" ]]; then
  echo "sub-memory-web not found at $WEB_BIN" >&2
  echo "Run bootstrap first: $PROJECT_DIR/skills/sub-memory-bootstrap/scripts/bootstrap_local.sh $PROJECT_DIR" >&2
  exit 1
fi

mkdir -p "$BASE_DIR"

cat <<EOF
Starting sub-memory web UI.

Project: $PROJECT_DIR
sub-memory base dir: $BASE_DIR
URL: http://$HOST:$PORT/ui

Open that URL directly in your browser after the server starts.
Press Ctrl+C to stop.
EOF

exec "$WEB_BIN" --base-dir "$BASE_DIR" --host "$HOST" --port "$PORT"
