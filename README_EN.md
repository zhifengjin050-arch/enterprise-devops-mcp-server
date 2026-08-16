# Enterprise DevOps MCP Server

[中文](README.md) | **English**

**Enterprise-grade AI DevOps automation server based on Model Context Protocol (MCP).**

Enable AI Agents (Cursor / Claude Desktop / custom clients) to safely operate infrastructure:

- Linux server inspection
- Docker container management
- SSH remote automation
- Kubernetes status queries
- Log analysis workflows
- Audit-ready security controls

> Suitable for: **open-source showcase** · **portfolio / interview demo** · **AI Ops experiments**

---

## Why this project?

Most AI coding assistants can *suggest* shell commands.  
This project lets an AI Agent **call governed DevOps tools** with:

1. **Read / Execute separation**
2. **Dangerous command filtering**
3. **Rate limiting & confirmation**
4. **Built-in audit trail**

One MCP Server can manage **local Docker** and **remote servers** under the same policy and the same audit log.

---

## Core Capabilities

### Server Monitoring

| Tool | Description |
|------|-------------|
| `get_server_health` | CPU / memory / disk / uptime / health grade |
| `get_system_info` | hostname / OS / platform / Python / uptime |
| `get_cpu_usage` | CPU percent + core count |
| `get_memory_usage` | total / used / available / percent |
| `get_disk_usage` | per-mount usage |
| `list_processes` | Top N processes by CPU |
| `get_audit_logs` | query recent tool calls + stats |

### Docker Management

| Tool | Access |
|------|--------|
| `docker_list` | READ |
| `docker_logs` | READ |
| `docker_restart` | EXECUTE |

### Kubernetes

| Tool | Access |
|------|--------|
| `k8s_get_pods` | READ |
| `k8s_get_deployments` | READ |
| `k8s_get_services` | READ |
| `k8s_logs` | READ |

### SSH Automation

| Tool | Access |
|------|--------|
| `ssh_check_connection` | READ |
| `ssh_execute_command` | EXECUTE |
| `ssh_upload_file` | EXECUTE |

### Security Control

- **Execute Permission Manager** — write tools disabled by default
- **Dangerous Command Filter** — blocks `rm -rf /`, `mkfs`, `shutdown`, ...
- **Audit mechanism** — every call recorded in memory ring buffer

Example: AI tries `rm -rf /` via SSH → blocked before remote execution:

```json
{
  "stdout": "",
  "stderr": "命令包含危险操作 'rm -rf /'，已被安全模块拦截",
  "status": "1"
}
```

---

## Architecture

```
Cursor / Claude / ChatGPT Client
              |
         MCP Client
              |
  Enterprise DevOps MCP Server
              |
   ---------------------------
   |           |             |
 System     Docker        SSH/K8s
 (local)    (local)       (remote)
```

See [docs/architecture.en.md](docs/architecture.en.md) and [docs/security.en.md](docs/security.en.md).  
中文文档：[架构](docs/architecture.md) · [安全](docs/security.md)

---

## Requirements

- Python **3.11+**
- Docker Desktop / Engine (for Docker tools)
- Optional: kubeconfig (Kubernetes tools)
- Optional: SSH reachability to remote hosts

---

## Installation

```bash
git clone https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server.git
cd enterprise-devops-mcp-server

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` for your environment. **Never commit `.env`.**

---

## Quick Start

### 1. Start MCP Server (stdio)

```bash
python -m app.server
# or
python scripts/run_devops_mcp.py
```

### 2. Configure Cursor MCP

Copy [examples/mcp_config_example.json](examples/mcp_config_example.json) into your Cursor MCP settings.

Minimal example:

```json
{
  "mcpServers": {
    "enterprise-devops": {
      "command": "python",
      "args": ["scripts/run_devops_mcp.py"],
      "cwd": "/absolute/path/to/enterprise-devops-mcp-server",
      "env": {
        "FASTMCP_SHOW_SERVER_BANNER": "false",
        "EXECUTE_TOOLS_ENABLED": "false"
      }
    }
  }
}
```

> Set `cwd` to your local clone path. Do not hard-code private machine paths in public docs.

### 3. Talk to the Agent

Examples:

- `Check current server health`
- `List running Docker containers`
- `Show recent logs for container test-nginx`
- `Try to run rm -rf / on the remote host` → should be **blocked**

---

## Security Design (must read)

Default:

```env
EXECUTE_TOOLS_ENABLED=false
```

| Mode | What AI can do |
|------|----------------|
| Default | Inspect only |
| `EXECUTE_TOOLS_ENABLED=true` | Restart containers / SSH execute / upload |
| `EXECUTE_PROTECTION_LEVEL=strict` | Rate limit + confirmation |

Production recommendation:

1. Keep execute **off** until needed
2. Prefer SSH keys over passwords
3. Never put production secrets in git
4. Review `get_audit_logs` after operations

Full details: [docs/security.en.md](docs/security.en.md)

---

## Screenshots

| # | Scenario |
|---|----------|
| 01 | MCP connection & tool discovery |
| 02 | AI server health inspection |
| 03 | Docker container inspection |
| 04 | MySQL log analysis via Docker logs |
| 05 | SSH dangerous command filter |
| 06 | Disk cleanup automation flow |

![01 MCP connection](docs/screenshots/01-mcp-connection-tools.png)

![02 Health check](docs/screenshots/02-server-health-check.png)

![03 Docker inspection](docs/screenshots/03-docker-inspection.png)

![04 MySQL log analysis](docs/screenshots/04-mysql-log-analysis.png)

![05 SSH danger filter](docs/screenshots/05-ssh-dangerous-command-filter.png)

![06 Disk cleanup](docs/screenshots/06-disk-cleanup-automation.png)

---

## Project Structure

```
enterprise-devops-mcp-server/
├── README.md              # Chinese (default)
├── README_EN.md           # English
├── LICENSE
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── app/
├── docs/
├── examples/
├── scripts/
└── tests/
```

---

## Testing

```bash
python -m pytest tests/ -v
```

Expected: **225+** tests passed.

```bash
docker compose --profile test run --rm mcp-server-test
```

---

## Environment Variables (summary)

| Variable | Default | Meaning |
|----------|---------|---------|
| `ENABLE_SECURITY` | `true` | master security switch |
| `EXECUTE_TOOLS_ENABLED` | `false` | allow write/execute tools |
| `ALLOWED_TOOLS` | `system,docker,kubernetes,ssh` | module whitelist |
| `EXECUTE_PROTECTION_LEVEL` | `basic` | `off` / `basic` / `strict` |
| `AUDIT_LOG_ENABLED` | `true` | enable audit buffer |
| `SSH_SERVERS` | empty | optional multi-host registry (no passwords) |

---

## Roadmap

| Version | Focus |
|---------|-------|
| **V1.0** | Local MCP + System/Docker/K8s/SSH + security + tests |
| **V1.1** | HTTP/SSE transport + auth + RBAC (enterprise remote access) |
| Later | Audit export, multi-tenant policy packs |

---

## Contributing

1. Fork & create a feature branch
2. Keep security defaults conservative
3. Add/adjust tests
4. Do not commit `.env`, keys, or real infrastructure identifiers

---

## License

[MIT](LICENSE)

---

## Disclaimer

This software can control servers and containers when execute mode is enabled.  
Use at your own risk. Always test in non-production first.  
Authors are not responsible for misuse or operational damage.
