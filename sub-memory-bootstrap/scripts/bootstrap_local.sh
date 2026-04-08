#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-$(pwd)}"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"

if [[ ! -f "$PROJECT_DIR/requirements.txt" ]]; then
  echo "requirements.txt not found in $PROJECT_DIR" >&2
  exit 1
fi

if [[ ! -f "$PROJECT_DIR/pyproject.toml" ]]; then
  echo "pyproject.toml not found in $PROJECT_DIR" >&2
  exit 1
fi

if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="python3.11"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
else
  echo "python3.11 or python3 is required" >&2
  exit 1
fi

cd "$PROJECT_DIR"

"$PYTHON_BIN" -m venv .venv
".venv/bin/python" -m pip install -r requirements.txt
".venv/bin/python" -m pip install -e .

if [[ -f ".env.example" && ! -f ".env" ]]; then
  cp .env.example .env
fi

cat <<EOF
Bootstrap complete.

Project: $PROJECT_DIR
Agent entrypoint: $PROJECT_DIR/.venv/bin/sub-memory-agent
MCP entrypoint: $PROJECT_DIR/.venv/bin/sub-memory-mcp

Next recommended checks:
  $PROJECT_DIR/.venv/bin/sub-memory-agent --help
  $PROJECT_DIR/.venv/bin/sub-memory-mcp --help
  $PROJECT_DIR/.venv/bin/python -m unittest discover -s tests
EOF

