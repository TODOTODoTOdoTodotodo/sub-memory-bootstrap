# sub-memory-bootstrap

Codex skill distribution repository for onboarding the local `sub-memory` project.

This repository publishes a reusable Codex skill that can:

- validate a local `sub-memory` checkout
- bootstrap the local Python environment
- confirm the install state
- generate ready-to-paste MCP config snippets for:
  - Codex
  - Gemini CLI
  - Claude Code

The actual skill lives in the [`sub-memory-bootstrap/`](./sub-memory-bootstrap) folder.

## What This Skill Is For

Use this skill when you already have a local checkout of the main `sub-memory` project and want a one-shot onboarding workflow for:

- local installation
- local `stdio` MCP server verification
- CLI integration snippet generation

Current scope:

- local install
- local stdio MCP
- CLI setup guidance

Not in scope:

- ChatGPT app integration
- Gemini app integration
- Claude app remote integration

## Repository Layout

```text
.
├── README.md
├── LICENSE
└── sub-memory-bootstrap/
    ├── SKILL.md
    └── scripts/
        ├── bootstrap_local.sh
        └── render_cli_snippets.py
```

## Install The Skill In Codex

Clone this repository:

```bash
git clone https://github.com/TODOTODoTOdoTodotodo/sub-memory-bootstrap.git
cd sub-memory-bootstrap
```

Install the skill into Codex:

```bash
mkdir -p ~/.codex/skills
cp -R sub-memory-bootstrap ~/.codex/skills/
```

Or install it as a symlink:

```bash
mkdir -p ~/.codex/skills
ln -s "$(pwd)/sub-memory-bootstrap" ~/.codex/skills/sub-memory-bootstrap
```

If you use a custom Codex home, install to `$CODEX_HOME/skills` instead of `~/.codex/skills`.

## What The Skill Does

The skill orchestrates three steps:

1. Validate that the target repository is really the `sub-memory` project.
2. Run a local bootstrap flow.
3. Render machine-specific MCP setup snippets.

### Bootstrap Script

The bundled bootstrap script expects the local `sub-memory` repository path as input.

```bash
./sub-memory-bootstrap/scripts/bootstrap_local.sh /absolute/path/to/sub-memory
```

It will:

- create `.venv`
- install `requirements.txt`
- install the project in editable mode
- create `.env` from `.env.example` when missing

### Config Snippet Renderer

```bash
python3 ./sub-memory-bootstrap/scripts/render_cli_snippets.py \
  --project-dir /absolute/path/to/sub-memory
```

It prints absolute-path snippets for:

- Codex
- Gemini CLI
- Claude Code
- Codex skill installation

## Example Prompts

After installing the skill in Codex, use prompts like:

```text
Use sub-memory-bootstrap to install this repo locally and generate Codex, Gemini CLI, and Claude Code MCP config snippets.
```

```text
Use sub-memory-bootstrap to validate the local setup and tell me the exact sub-memory-mcp path for this repo.
```

```text
Use sub-memory-bootstrap to inspect this repo, verify the local install path, and draft a short onboarding note for another engineer.
```

## Expected Target Project

This skill is designed for the main `sub-memory` repository, where the target project contains:

- `requirements.txt`
- `pyproject.toml`
- `mcp_server.py`
- `.env.example`

The skill does not bundle the `sub-memory` application itself. It only provides the Codex onboarding layer.

## License

MIT. See [LICENSE](./LICENSE).

