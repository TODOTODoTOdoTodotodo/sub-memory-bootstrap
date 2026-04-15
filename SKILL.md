---
name: sub-memory-bootstrap
description: Use when the user wants to install or validate the local sub-memory project, finish project-scoped Codex MCP registration, update AGENTS.md with sub_memory usage rules, start the local stdio MCP server, start the local web UI, or generate ready-to-paste Codex, Gemini CLI, and Claude Code config snippets.
---

# Sub-memory Bootstrap

This repository root is also installable as a Codex skill so GitHub-based installers can target `--path .`.

Use this skill for end-to-end local onboarding of the `sub-memory` repository.

## Workflow

1. Resolve the repository root and confirm these files exist:
   `requirements.txt`, `pyproject.toml`, `mcp_server.py`, `.env.example`
2. If the local install is missing or stale, run:
   `skills/sub-memory-bootstrap/scripts/bootstrap_local.sh <repo-root>`
3. The bootstrap flow must also finish project-local Codex onboarding:
   write `.codex/config.toml` for `sub_memory` MCP registration and update `AGENTS.md`
   with `sub_memory` usage rules.
   Seed a new repository `AGENTS.md` from the bundled default template when needed.
4. Generate machine-specific config snippets with:
   `skills/sub-memory-bootstrap/scripts/render_cli_snippets.py --project-dir <repo-root>`
5. If the user asks for the web UI, start it with:
   `skills/sub-memory-bootstrap/scripts/start_web_ui.sh <repo-root>`
   and report the browser URL.
6. Validate the install with:
   `sub-memory-agent --help`
   `sub-memory-mcp --help`
   `sub-memory-web --help`
   `python -m unittest discover -s tests`
7. Use project-scoped Codex configuration by default.
   Do not edit `~/.codex/config.toml`, `~/.gemini/settings.json`, `.mcp.json`, or other user-global config files without explicit permission.
8. For Codex sessions, the generated `AGENTS.md` rules should mirror the `local_agent`
   post-processing flow: recall before answering, store after each substantive turn,
   reinforce after the answer when recall materially helped, and compact long
   multi-turn sessions into a short working summary.
9. If the user is working in Korean, keep the explanation in Korean.
   Preserve commands, paths, config keys, and tool names exactly as written.

## What To Produce

- Local install status
- Exact `sub-memory-mcp` path
- Exact `sub-memory-web` path
- If started, the exact local browser URL
- Exact project Codex config path
- Confirmation that `AGENTS.md` contains the `sub_memory` usage rules
- Ready-to-paste snippets for:
  - Codex
  - Gemini CLI
  - Claude Code
- Any blockers such as missing `sqlite-vec`, missing `.env`, or incompatible Python

## Skill Installation

If the user wants this skill installed globally for Codex, install either of these:

- repository root via `--path .`
- nested skill via `--path skills/sub-memory-bootstrap`

Both layouts expose the same workflow and scripts.
