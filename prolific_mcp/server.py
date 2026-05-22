"""Prolific MCP 서버 엔트리포인트 (stdio).

실행:
    uv run python -m prolific_mcp.server
"""

from __future__ import annotations

from dotenv import load_dotenv
from fastmcp import FastMCP

from .client import ProlificClient
from .tools import register_tools


def main() -> None:
    load_dotenv()
    mcp = FastMCP("prolific")
    client = ProlificClient()
    register_tools(mcp, client)
    mcp.run()


if __name__ == "__main__":
    main()
