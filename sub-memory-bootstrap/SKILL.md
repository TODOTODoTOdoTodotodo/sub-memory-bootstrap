---
name: sub-memory-bootstrap
description: Use when the user wants to install or validate the local sub-memory project, start the local stdio MCP server, generate ready-to-paste Codex, Gemini CLI, and Claude Code config snippets, or install the bundled Codex skill for one-shot onboarding.
---

# Sub-memory Bootstrap

Use this skill for end-to-end local onboarding of the `sub-memory` repository.

## Workflow

1. Resolve the repository root and confirm these files exist:
   `requirements.txt`, `pyproject.toml`, `mcp_server.py`, `.env.example`
2. If the local install is missing or stale, run:
   `scripts/bootstrap_local.sh <repo-root>`
3. Generate machine-specific config snippets with:
   `scripts/render_cli_snippets.py --project-dir <repo-root>`
4. Validate the install with:
   `sub-memory-agent --help`
   `sub-memory-mcp --help`
   `python -m unittest discover -s tests`
5. When the user asks for actual client integration, provide snippets first.
   Do not edit `~/.codex/config.toml`, `~/.gemini/settings.json`, `.mcp.json`, or other user-global config files without explicit permission.

## What To Produce

- Local install status
- Exact `sub-memory-mcp` path
- Ready-to-paste snippets for:
  - Codex
  - Gemini CLI
  - Claude Code
- Any blockers such as missing `sqlite-vec`, missing `.env`, or incompatible Python

## Skill Installation

If the user wants this skill installed globally for Codex, copy or symlink this folder to:

- `$CODEX_HOME/skills/sub-memory-bootstrap`
- or `~/.codex/skills/sub-memory-bootstrap`

## Scope

- In scope: local install, stdio MCP, CLI setup, verification, documentation snippets
- Out of scope: ChatGPT app, Gemini app, Claude app remote integrations

