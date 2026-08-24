#!/usr/bin/env python3
"""List 17 MCP tools and the read-only execute gate. No network, no secrets."""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("EXECUTE_TOOLS_ENABLED", "false")

from app.tools.metadata import list_tool_metadata  # noqa: E402


def main() -> int:
    tools = list_tool_metadata()
    enabled = os.environ.get("EXECUTE_TOOLS_ENABLED", "false")
    print(f"EXECUTE_TOOLS_ENABLED={enabled}")
    print(f"tools={len(tools)}")
    print(f"{'name':<24} {'category':<12} {'risk':<12} permission")
    for t in tools:
        print(f"{t['name']:<24} {t['category']:<12} {t['risk_level']:<12} {t['required_permission']}")
    print("Demo next: cp .env.example .env && python scripts/run_devops_mcp.py")
    print("Do not commit .env, kubeconfig, or SSH keys.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
