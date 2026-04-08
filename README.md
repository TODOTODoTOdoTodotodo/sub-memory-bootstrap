# sub-memory-bootstrap

Codex skill distribution repository for onboarding the local `sub-memory` project.

This repository publishes a reusable Codex skill that can:

- validate a local `sub-memory` checkout
- bootstrap the local Python environment
- confirm the install state
- write project-scoped Codex MCP registration
- update `AGENTS.md` with `sub_memory` usage rules
- generate ready-to-paste MCP config snippets for:
  - Codex
  - Gemini CLI
  - Claude Code

The actual skill lives in the [`sub-memory-bootstrap/`](./sub-memory-bootstrap) folder.

## What This Skill Is For

Use this skill when you already have a local checkout of the main `sub-memory` project and want a one-shot onboarding workflow for:

- local installation
- local `stdio` MCP server verification
- project-scoped Codex onboarding
- CLI integration snippet generation

Current scope:

- local install
- local stdio MCP
- project-local `.codex/config.toml`
- `AGENTS.md` rule update
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
        ├── configure_codex_project.py
        └── render_cli_snippets.py
    └── templates/
        └── AGENTS.default.md
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
2. Run a local bootstrap flow and finish project-local Codex onboarding.
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
- write `.codex/config.toml` for project-scoped `sub_memory` MCP registration
- seed a new `AGENTS.md` from the bundled default template when needed
- update `AGENTS.md` with `sub_memory` usage rules
  - recall before answering
  - store after each substantive turn
  - reinforce after the answer when recall materially helped

### Project Codex Registration

```bash
python3 ./sub-memory-bootstrap/scripts/configure_codex_project.py \
  --project-dir /absolute/path/to/sub-memory
```

It will:

- create or update `/absolute/path/to/sub-memory/.codex/config.toml`
- create or update `/absolute/path/to/sub-memory/AGENTS.md`
- preserve unrelated existing content in both files

### Config Snippet Renderer

```bash
python3 ./sub-memory-bootstrap/scripts/render_cli_snippets.py \
  --project-dir /absolute/path/to/sub-memory
```

It prints absolute-path snippets for:

- Codex
- Gemini CLI
- Claude Code
- project-scoped Codex registration

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

## 한국어 사용자용 예시

한글로 요청해도 같은 workflow로 동작합니다. 설명은 한국어로 유지하고, 명령어와 설정 키는 그대로 두는 방식이 가장 안정적입니다.

```text
sub-memory-bootstrap을 사용해서 이 저장소를 로컬에 설치하고 Codex, Gemini CLI, Claude Code용 MCP 설정 스니펫을 현재 머신 경로 기준으로 작성해줘.
```

```text
sub-memory-bootstrap으로 기존 설치 상태를 점검하고, 이 저장소에서 실제로 실행되는 sub-memory-mcp 경로를 알려줘.
```

```text
sub-memory-bootstrap으로 로컬 stdio MCP 서버가 바로 쓸 수 있는 상태인지 확인하고, project-local Codex 설정과 AGENTS.md까지 준비해줘.
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
