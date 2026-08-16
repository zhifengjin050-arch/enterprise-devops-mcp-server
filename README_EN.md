# Enterprise DevOps MCP Server

[中文](README.md) | **English**

> **V1.0.1** · MIT · [Architecture](docs/architecture.en.md) · [Security](docs/security.en.md) · [Contributing](CONTRIBUTING.md)

---

## Positioning

**Enterprise AI DevOps MCP Server enables AI Agents to securely operate infrastructure through MCP protocol.**

An enterprise AI Ops Agent Server on MCP — Agents manage Linux, Docker, Kubernetes, and SSH **within governed security controls**.

---

## Why This Project

Traditional:

```
Engineer → SSH → Manual Command
```

This project:

```
AI Agent → MCP Protocol → Security Layer → Infrastructure
```

**AI does not own raw server privileges.** Every call goes through Permission Control, Execute Protection, Command Filtering, and Audit Logging.

---

## Features

### Infrastructure Management

- Linux monitoring (CPU / Memory / Disk / Process)
- Docker (list / logs / restart)
- Kubernetes (Pods / Deployments / Services / Logs)
- SSH (check / execute / upload)

**17 MCP Tools**

### Enterprise Security

- Permission: `READ_ONLY` / `EXECUTE`
- Execute Protection: `OFF` / `BASIC` / `STRICT`
- Dangerous Command Filter — `rm -rf /` blocked before remote execution
- Audit Logging

---

## Quick Start

```bash
git clone https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server.git
cd enterprise-devops-mcp-server
pip install -r requirements.txt
cp .env.example .env
python -m app.server
```

Cursor MCP: set `cwd` to `YOUR_PROJECT_PATH` — see `mcp_config_examples/cursor_mcp.json`.

---

## Screenshots

See [README.md](README.md#screenshots) / [docs/screenshots](docs/screenshots/).

---

## License

[MIT](LICENSE)
