# Changelog

All notable changes to this project are documented in this file.

---

## [v1.0.1](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/releases/tag/v1.0.1) — 2026-08-17

### Added

- Enterprise AI DevOps **MCP Server** (FastMCP / stdio)
- **17 MCP Tools**
  - System: monitoring, health, processes, audit query
  - Docker: list, logs, restart
  - Kubernetes: pods, deployments, services, logs
  - SSH: connection check, remote command, secure upload
- **Enterprise Security Architecture**
  - Permission Control (`READ_ONLY` / `EXECUTE`)
  - Execute Protection (`OFF` / `BASIC` / `STRICT`)
  - Dangerous Command Filter
  - Audit Logging
- Docker multi-stage image + Compose
- GitHub Actions CI (`pytest` on push / pull_request)
- Bilingual docs, screenshots, contributing guide

### Testing

- **225 tests passed**

### Security defaults

- `EXECUTE_TOOLS_ENABLED=false`
- Example: `rm -rf /` blocked before remote execution
