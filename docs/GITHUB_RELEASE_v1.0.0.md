# GitHub Release — v1.0.x

## Initial Release

Enterprise DevOps MCP Server: governed AI Agent tools for Linux, Docker, Kubernetes, and SSH.

Current tag line: **v1.0.1** (225 tests). This note describes the 1.0 product.

## Core Features

- 17 MCP tools
- Security layer: RBAC, execute gate, command filter, audit
- Read-only default (`EXECUTE_TOOLS_ENABLED=false`)
- Cursor / Claude MCP client support

## Deployment Support

```bash
cp .env.example .env
python -m app.server
# or
docker compose up -d --build
```
