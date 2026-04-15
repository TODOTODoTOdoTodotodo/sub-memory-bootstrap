from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "sub-memory-bootstrap"
    / "scripts"
    / "configure_codex_project.py"
)


def load_module():
    spec = importlib.util.spec_from_file_location(
        "configure_codex_project",
        SCRIPT_PATH,
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConfigureCodexProjectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)
        (self.project_dir / "requirements.txt").write_text("", encoding="utf-8")
        (self.project_dir / "pyproject.toml").write_text("", encoding="utf-8")
        (self.project_dir / "mcp_server.py").write_text("", encoding="utf-8")
        mcp_entrypoint = self.project_dir / ".venv" / "bin" / "sub-memory-mcp"
        mcp_entrypoint.parent.mkdir(parents=True, exist_ok=True)
        mcp_entrypoint.write_text("#!/bin/sh\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_configure_project_creates_codex_config_and_agents(self) -> None:
        paths = self.module.configure_project(self.project_dir)

        config_text = paths["config_path"].read_text(encoding="utf-8")
        agents_text = paths["agents_path"].read_text(encoding="utf-8")

        self.assertIn("[mcp_servers.sub_memory]", config_text)
        self.assertIn(str(self.project_dir / ".venv" / "bin" / "sub-memory-mcp"), config_text)
        self.assertIn("## sub_memory MCP", agents_text)
        self.assertIn("get_memory_status", agents_text)
        self.assertIn("compact the active thread", agents_text)

    def test_configure_project_preserves_existing_content(self) -> None:
        config_path = self.project_dir / ".codex" / "config.toml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            '[profiles.default]\nmodel = "gpt-5"\n\n'
            '[mcp_servers.sub_memory]\ncommand = "/tmp/old"\n',
            encoding="utf-8",
        )
        agents_path = self.project_dir / "AGENTS.md"
        agents_path.write_text(
            "# Custom Notes\n\nDo not remove this section.\n",
            encoding="utf-8",
        )

        self.module.configure_project(self.project_dir)

        config_text = config_path.read_text(encoding="utf-8")
        agents_text = agents_path.read_text(encoding="utf-8")

        self.assertIn('[profiles.default]\nmodel = "gpt-5"', config_text)
        self.assertEqual(config_text.count("[mcp_servers.sub_memory]"), 1)
        self.assertIn("# Custom Notes", agents_text)
        self.assertIn("Do not remove this section.", agents_text)
        self.assertIn("## sub_memory MCP", agents_text)
        self.assertIn("compact the active thread", agents_text)
