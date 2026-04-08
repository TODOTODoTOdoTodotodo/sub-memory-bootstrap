#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def resolve_paths(project_dir: Path) -> dict[str, str]:
    project_dir = project_dir.resolve()
    script_dir = Path(__file__).resolve().parent
    venv_bin = project_dir / ".venv" / "bin"
    mcp_entrypoint = venv_bin / "sub-memory-mcp"
    codex_config_path = project_dir / ".codex" / "config.toml"
    agents_path = project_dir / "AGENTS.md"
    configure_script = script_dir / "configure_codex_project.py"
    return {
        "project_dir": str(project_dir),
        "mcp_entrypoint": str(mcp_entrypoint),
        "codex_config_path": str(codex_config_path),
        "agents_path": str(agents_path),
        "configure_script": str(configure_script),
    }


def build_output(paths: dict[str, str]) -> str:
    project_dir = paths["project_dir"]
    mcp_entrypoint = paths["mcp_entrypoint"]
    codex_config_path = paths["codex_config_path"]
    agents_path = paths["agents_path"]
    configure_script = paths["configure_script"]

    return f"""# sub-memory local onboarding snippets

## Codex project registration

```bash
python3 {configure_script} --project-dir {project_dir}
```

This writes:

- `{codex_config_path}`
- `{agents_path}`

## Codex

```toml
[mcp_servers.sub_memory]
command = "{mcp_entrypoint}"
args = ["--base-dir", "{project_dir}"]
cwd = "{project_dir}"
enabled_tools = ["recall_associated_memory", "store_memory", "reinforce_memory", "get_memory_status"]
startup_timeout_sec = 30
tool_timeout_sec = 120
```

## Gemini CLI

```json
{{
  "mcpServers": {{
    "sub_memory": {{
      "command": "{mcp_entrypoint}",
      "args": ["--base-dir", "{project_dir}"],
      "cwd": "{project_dir}",
      "timeout": 30000
    }}
  }}
}}
```

## Claude Code

```bash
claude mcp add --transport stdio sub-memory -- \\
  {mcp_entrypoint} \\
  --base-dir {project_dir}
```

## Next step

Start a new Codex session from `{project_dir}` so the project-scoped MCP config and
`AGENTS.md` instructions are loaded together.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Render local sub-memory CLI snippets")
    parser.add_argument(
        "--project-dir",
        default=str(Path.cwd()),
        help="Repository root containing .venv and pyproject.toml.",
    )
    args = parser.parse_args()

    paths = resolve_paths(Path(args.project_dir))
    print(build_output(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
