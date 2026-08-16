#!/usr/bin/env python3
"""Cross-platform launcher for Enterprise DevOps MCP Server.

Usage:
    python scripts/run_devops_mcp.py

Or configure Cursor MCP to:
    command: python
    args: ["scripts/run_devops_mcp.py"]
    cwd: <project root>
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    # Keep stdout clean for MCP stdio JSON-RPC
    os.environ.setdefault("FASTMCP_SHOW_SERVER_BANNER", "false")
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    from app.server import main as server_main

    server_main()


if __name__ == "__main__":
    main()
