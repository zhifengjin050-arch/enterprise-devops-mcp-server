# Changelog

All notable changes to this project are documented in this file.

---

## v1.0.1

### Added

- MCP Server（FastMCP / stdio）
- System tools（monitoring, health, processes, audit query）
- Docker tools（list, logs, restart）
- Kubernetes tools（pods, deployments, services, logs）
- SSH tools（connection check, remote command, secure upload）
- Security framework（Permission Control, Execute Protection, Command Filter）
- Audit logging
- Docker deployment（multi-stage image + Compose）
- Open-source docs（README, architecture, security, screenshots）
- GitHub Actions pytest workflow

### Testing

- **225 tests passed**

### Security defaults

- `EXECUTE_TOOLS_ENABLED=false`
- Dangerous command blocked before remote execution（e.g. `rm -rf /`）
