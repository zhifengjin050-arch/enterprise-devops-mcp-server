# Enterprise DevOps MCP Server

[中文](README.md) | **English**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-225%20passed-brightgreen.svg)](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/actions/workflows/test.yml)
[![CI](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/actions/workflows/test.yml/badge.svg)](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/actions/workflows/test.yml)
[![MCP](https://img.shields.io/badge/MCP-compatible-8A2BE2.svg)](https://modelcontextprotocol.io/)
[![Release](https://img.shields.io/github/v/release/zhifengjin050-arch/enterprise-devops-mcp-server)](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/releases/tag/v1.0.1)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Enterprise AI DevOps MCP Server for secure infrastructure automation with MCP, Docker, Kubernetes and SSH.**

Give AI Agents a governed path to operate infrastructure — not an unrestricted shell.

> **AI Agent → MCP Server → Security Layer → Infrastructure**

[Architecture](docs/architecture.en.md) · [Security](docs/security.en.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Release v1.0.1](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/releases/tag/v1.0.1)

---

## Why This Project

### Traditional ops

- Engineers run SSH commands by hand
- Privileges are hard to bound once a shell is exposed
- Changes often leave weak or missing audit trails

```
Engineer → SSH → Manual Command
```

### AI DevOps with this server

```
AI Agent
   ↓
MCP Tool
   ↓
Security Layer
   ↓
Infrastructure
```

The model never “owns” the host. Every call goes through permission checks, execute protection, command filtering, and audit logging.

---

## Features

| Feature | Status |
|---------|--------|
| Linux Monitoring | ✅ |
| Docker Management | ✅ |
| Kubernetes | ✅ |
| SSH Automation | ✅ |
| Permission Control | ✅ |
| Execute Protection | ✅ |
| Audit Logging | ✅ |
| Docker Deployment | ✅ |
| GitHub Actions CI | ✅ |

**17 MCP tools** across System, Docker, Kubernetes, and SSH.

---

## Security

Safe by default:

```env
EXECUTE_TOOLS_ENABLED=false
```

- **ReadOnly / Execute separation**
- **Execute disabled unless an admin opts in**
- **Dangerous command filtering** (blocked before SSH connect)
- **Audit trail** for tool calls

Example:

```
rm -rf /
   ↓
Blocked by the security module
(no remote SSH session is opened)
```

Details: [docs/security.en.md](docs/security.en.md)

---

## Architecture

```
                 AI Agent
                    |
              MCP Protocol
                    |
        Enterprise DevOps MCP Server
                    |
 ------------------------------------------------
 |              |              |                |
System        Docker       Kubernetes        SSH
                    |
              Security Layer
```

---

## Screenshots

See the gallery in the [Chinese README](README.md#screenshots) or [docs/screenshots](docs/screenshots/).

---

## Quick Start

```bash
git clone https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server.git
cd enterprise-devops-mcp-server

pip install -r requirements.txt
cp .env.example .env

python -m app.server
```

### Cursor MCP

Replace `YOUR_PROJECT_PATH` with your local absolute path — never commit real machine paths:

```json
{
  "mcpServers": {
    "enterprise-devops": {
      "command": "python",
      "args": ["scripts/run_devops_mcp.py"],
      "cwd": "YOUR_PROJECT_PATH",
      "env": {
        "FASTMCP_SHOW_SERVER_BANNER": "false",
        "EXECUTE_TOOLS_ENABLED": "false"
      }
    }
  }
}
```

### Tests

```bash
pytest
```

### Docker

```bash
docker compose up -d --build
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Keep `EXECUTE_TOOLS_ENABLED=false` as the default.

---

## License

[MIT](LICENSE)
