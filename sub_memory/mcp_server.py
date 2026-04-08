from __future__ import annotations

import argparse
import logging
from pathlib import Path
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from sub_memory.config import Settings
from sub_memory.service import MemoryService


MCP_INSTRUCTIONS = """Local memory tools backed by SQLite, sqlite-vec, networkx, and local embeddings.

Use recall_associated_memory to fetch relevant prior memory before answering.
After each substantive turn, call store_memory with the latest user request and your final answer unless the current host runtime already stores turns automatically.
Use reinforce_memory after the answer when recalled memory materially influenced the answer.
If a multi-turn session grows long, compact the active thread into a short working summary and rely on that summary plus recalled memory instead of the full raw transcript.
"""


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def build_mcp_server(
    service: MemoryService,
    *,
    log_level: str = "INFO",
    host: str = "127.0.0.1",
    port: int = 8000,
) -> FastMCP:
    server = FastMCP(
        "sub-memory",
        instructions=MCP_INSTRUCTIONS,
        log_level=log_level.upper(),
        host=host,
        port=port,
    )

    @server.tool(
        name="recall_associated_memory",
        description=(
            "Recall the most similar memory for a query and expand related memories "
            "through the weighted graph."
        ),
        structured_output=True,
    )
    def recall_associated_memory(query: str, depth: int = 2) -> dict[str, Any]:
        """Recall related memory nodes for a natural-language query."""
        return service.recall_associated_memory(query=query, depth=depth)

    @server.tool(
        name="store_memory",
        description=(
            "Store a user/assistant exchange in local long-term memory and connect it "
            "to the previous turn."
        ),
        structured_output=True,
    )
    def store_memory(user_text: str, ai_response: str) -> dict[str, Any]:
        """Persist a new memory node using the provided conversation turn."""
        return service.store_memory(user_text=user_text, ai_response=ai_response)

    @server.tool(
        name="reinforce_memory",
        description=(
            "Increase association weights between memory nodes that were useful "
            "together."
        ),
        structured_output=True,
    )
    def reinforce_memory(node_ids: list[str]) -> dict[str, Any]:
        """Increase edge weights between the provided memory node IDs."""
        return service.reinforce_memory(node_ids=node_ids)

    @server.tool(
        name="get_memory_status",
        description=(
            "Return local memory store status for installation validation and "
            "operational debugging."
        ),
        structured_output=True,
    )
    def get_memory_status() -> dict[str, Any]:
        """Expose the current local memory store configuration and node count."""
        return service.get_status()

    return server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="sub-memory MCP server")
    parser.add_argument(
        "--base-dir",
        default=str(Path.cwd()),
        help="Project directory containing .env and memory.db.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default="stdio",
        help="MCP transport. Local agent integrations should use stdio.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP-based transports.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP-based transports.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="Logging level written to stderr.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.log_level)

    try:
        settings = Settings.from_env(Path(args.base_dir))
        service = MemoryService.from_settings(settings)
    except Exception as exc:
        logging.getLogger(__name__).error("Failed to initialize memory service: %s", exc)
        return 1

    try:
        server = build_mcp_server(
            service,
            log_level=args.log_level,
            host=args.host,
            port=args.port,
        )
        server.run(transport=args.transport)
        return 0
    except Exception as exc:
        logging.getLogger(__name__).error("MCP server failed: %s", exc)
        return 1
    finally:
        service.close()
