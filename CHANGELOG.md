# Changelog

All notable changes to this project are documented in this file.

---

## [v1.0.2] hardening

- SSH 执行/上传传入 password；无密码时启用密钥与 agent
- `SSH_HOST_KEY_POLICY=reject` 时仅信任 known_hosts
- 拦截管道进 shell、敏感本地路径上传，并限制上传体积与日志行数
- 新增 `confirm_execute_action`，使 STRICT 模式可被 Agent 完成确认
- 工具错误对调用方返回稳定文案；stdio 信任模型在启动日志中写明

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
