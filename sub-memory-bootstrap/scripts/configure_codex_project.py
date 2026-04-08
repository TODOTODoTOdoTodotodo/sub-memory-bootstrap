#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re


CONFIG_BEGIN = "# BEGIN SUB-MEMORY MCP"
CONFIG_END = "# END SUB-MEMORY MCP"
AGENTS_BEGIN = "<!-- BEGIN SUB-MEMORY MCP RULES -->"
AGENTS_END = "<!-- END SUB-MEMORY MCP RULES -->"
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_AGENTS_TEMPLATE = SCRIPT_DIR.parent / "templates" / "AGENTS.default.md"


def resolve_project_dir(project_dir: Path) -> Path:
    resolved = project_dir.resolve()
    required = ("requirements.txt", "pyproject.toml", "mcp_server.py")
    missing = [name for name in required if not (resolved / name).exists()]
    if missing:
        raise RuntimeError(
            "Target project is missing required files: " + ", ".join(missing)
        )
    return resolved


def build_codex_block(project_dir: Path) -> str:
    mcp_entrypoint = project_dir / ".venv" / "bin" / "sub-memory-mcp"
    if not mcp_entrypoint.exists():
        raise RuntimeError(
            f"Expected MCP entrypoint at {mcp_entrypoint}. Run the bootstrap step first."
        )

    return (
        f"{CONFIG_BEGIN}\n"
        "# Managed by sub-memory-bootstrap. Re-run the skill to refresh.\n"
        "[mcp_servers.sub_memory]\n"
        f'command = "{mcp_entrypoint}"\n'
        f'args = ["--base-dir", "{project_dir}"]\n'
        f'cwd = "{project_dir}"\n'
        'enabled_tools = ["recall_associated_memory", "store_memory", '
        '"reinforce_memory", "get_memory_status"]\n'
        "startup_timeout_sec = 30\n"
        "tool_timeout_sec = 120\n"
        f"{CONFIG_END}\n"
    )


def build_agents_block() -> str:
    return (
        f"{AGENTS_BEGIN}\n"
        "## sub_memory MCP\n\n"
        "- If the `sub_memory` MCP server is available, call `get_memory_status` "
        "before implementation, debugging, review, or planning tasks that may depend "
        "on prior project memory.\n"
        "- Use `recall_associated_memory` before answering when prior design "
        "decisions, integration history, or TODO context may matter.\n"
        "- After each substantive turn, call `store_memory` with the latest user "
        "request and the final assistant answer or a faithful summary of it, unless "
        "the turn is empty, purely mechanical, or the current runtime already stores "
        "it automatically.\n"
        "- Use `reinforce_memory` after the answer when recalled memory materially "
        "influenced the final answer or code change.\n"
        "- When a multi-turn session gets long or repetitive, compact the active "
        "thread into a short working summary and continue from that summary plus "
        "`sub_memory` recall instead of depending on the full raw transcript.\n"
        "- If `sub_memory` tools are missing in the current Codex session, explain "
        "that project-scoped MCP registration is stored in `.codex/config.toml` and "
        "that starting a new Codex session from the repository root may be required "
        "after running `sub-memory-bootstrap`.\n"
        f"{AGENTS_END}\n"
    )


def load_default_agents_header() -> str:
    if not DEFAULT_AGENTS_TEMPLATE.exists():
        raise RuntimeError(
            f"Missing default AGENTS template: {DEFAULT_AGENTS_TEMPLATE}"
        )
    return DEFAULT_AGENTS_TEMPLATE.read_text(encoding="utf-8").rstrip()


def _replace_or_append_block(
    existing: str,
    *,
    begin: str,
    end: str,
    block: str,
) -> str:
    if begin in existing and end in existing:
        prefix, remainder = existing.split(begin, 1)
        _old_block, suffix = remainder.split(end, 1)
        rebuilt = prefix.rstrip()
        if rebuilt:
            rebuilt += "\n\n"
        rebuilt += block.rstrip() + "\n"
        suffix = suffix.lstrip("\n")
        if suffix:
            rebuilt += "\n" + suffix
        return rebuilt

    stripped = existing.rstrip()
    if not stripped:
        return block.rstrip() + "\n"
    return stripped + "\n\n" + block.rstrip() + "\n"


def upsert_codex_config(project_dir: Path) -> Path:
    config_path = project_dir / ".codex" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    existing = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    block = build_codex_block(project_dir)
    bare_table_pattern = re.compile(
        r"(?ms)^\[mcp_servers\.sub_memory\]\n.*?(?=^\[|\Z)"
    )

    if CONFIG_BEGIN in existing and CONFIG_END in existing:
        updated = _replace_or_append_block(
            existing,
            begin=CONFIG_BEGIN,
            end=CONFIG_END,
            block=block,
        )
    elif bare_table_pattern.search(existing):
        updated = bare_table_pattern.sub(block.rstrip() + "\n\n", existing, count=1).rstrip() + "\n"
    else:
        updated = _replace_or_append_block(
            existing,
            begin=CONFIG_BEGIN,
            end=CONFIG_END,
            block=block,
        )

    config_path.write_text(updated, encoding="utf-8")
    return config_path


def upsert_agents_md(project_dir: Path) -> Path:
    agents_path = project_dir / "AGENTS.md"
    existing = agents_path.read_text(encoding="utf-8") if agents_path.exists() else ""
    block = build_agents_block()

    if not existing.strip():
        updated = load_default_agents_header() + "\n\n" + block.rstrip() + "\n"
    else:
        updated = _replace_or_append_block(
            existing,
            begin=AGENTS_BEGIN,
            end=AGENTS_END,
            block=block,
        )

    agents_path.write_text(updated, encoding="utf-8")
    return agents_path


def configure_project(project_dir: Path) -> dict[str, Path]:
    resolved = resolve_project_dir(project_dir)
    return {
        "config_path": upsert_codex_config(resolved),
        "agents_path": upsert_agents_md(resolved),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Write project-scoped Codex MCP config and AGENTS.md rules."
    )
    parser.add_argument(
        "--project-dir",
        default=str(Path.cwd()),
        help="Repository root containing .venv and pyproject.toml.",
    )
    args = parser.parse_args()

    paths = configure_project(Path(args.project_dir))
    print(f"Codex project config: {paths['config_path']}")
    print(f"AGENTS rules updated: {paths['agents_path']}")
    print("Start a new Codex session from the repository root to load both files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
