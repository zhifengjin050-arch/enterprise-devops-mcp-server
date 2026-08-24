#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi
export EXECUTE_TOOLS_ENABLED=false
python scripts/demo_list_tools.py
if command -v docker >/dev/null 2>&1; then
  docker compose up -d --build
  echo "MCP compose is up. Keep EXECUTE_TOOLS_ENABLED=false unless you have change control."
else
  echo "docker not found; run: python scripts/run_devops_mcp.py"
fi
