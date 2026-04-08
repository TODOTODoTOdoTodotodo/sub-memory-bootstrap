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
6. If the user is working in Korean, keep the explanation in Korean.
   Preserve commands, paths, config keys, and tool names exactly as written.

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

## Korean Prompt Examples

Use the same workflow for Korean-language requests such as:

- `sub-memory-bootstrap을 사용해서 이 저장소를 로컬에 설치하고 Codex, Gemini CLI, Claude Code 설정 스니펫까지 만들어줘.`
- `sub-memory-bootstrap으로 현재 설치 상태를 점검하고 이 저장소의 sub-memory-mcp 실제 경로를 알려줘.`
- `sub-memory-bootstrap으로 로컬 MCP 서버가 바로 쓸 수 있는 상태인지 확인하고, 다른 개발자에게 전달할 짧은 설치 메모도 작성해줘.`
