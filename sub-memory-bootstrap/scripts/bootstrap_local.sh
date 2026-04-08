#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
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

".venv/bin/python" "$SCRIPT_DIR/configure_codex_project.py" \
  --project-dir "$PROJECT_DIR"

cat <<EOF
Bootstrap complete.

Project: $PROJECT_DIR
Agent entrypoint: $PROJECT_DIR/.venv/bin/sub-memory-agent
MCP entrypoint: $PROJECT_DIR/.venv/bin/sub-memory-mcp
Codex project config: $PROJECT_DIR/.codex/config.toml
AGENTS rules: $PROJECT_DIR/AGENTS.md

Next recommended checks:
  $PROJECT_DIR/.venv/bin/sub-memory-agent --help
  $PROJECT_DIR/.venv/bin/sub-memory-mcp --help
  $PROJECT_DIR/.venv/bin/python -m unittest discover -s tests
  Start a new Codex session from $PROJECT_DIR
EOF
