# Enterprise DevOps MCP Server

**中文** | [English](README_EN.md)

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-225%20passed-brightgreen.svg)](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/actions/workflows/test.yml)
[![CI](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/actions/workflows/test.yml/badge.svg)](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/actions/workflows/test.yml)
[![MCP](https://img.shields.io/badge/MCP-compatible-8A2BE2.svg)](https://modelcontextprotocol.io/)
[![Release](https://img.shields.io/github/v/release/zhifengjin050-arch/enterprise-devops-mcp-server)](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/releases/tag/v1.0.1)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Enterprise AI DevOps MCP Server for secure infrastructure automation with MCP, Docker, Kubernetes and SSH.**

基于 **MCP（Model Context Protocol）** 的企业级 AI 运维 Agent Server：  
让 AI Agent 在安全控制下管理 Linux、Docker、Kubernetes 与 SSH 基础设施。

> **AI Agent → MCP Server → Security Layer → Infrastructure**

[Architecture](docs/architecture.md) · [Security](docs/security.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md) · [Release Notes](RELEASE_NOTES_v1.0.1.md)

---

## Why This Project

### 传统运维

| 痛点 | 表现 |
|------|------|
| SSH 手动执行 | 工程师逐条敲命令，难规模化 |
| 权限不可控 | 模型或脚本一旦拿到 shell，几乎等同 root |
| 缺少审计 | 谁改了什么、何时执行，事后难追溯 |

```
Engineer → SSH → Manual Command
```

### AI DevOps（本项目）

```
AI Agent
   ↓
MCP Tool
   ↓
Security Layer
   ↓
Infrastructure
```

**AI 不直接拥有服务器权限。** 每次调用都经过 Permission Control、Execute Protection、Command Filtering 与 Audit Logging。

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

**MCP Tools：17**（System 7 · Docker 3 · Kubernetes 4 · SSH 3）

---

## Security

企业级默认：**只读运维**。

```env
EXECUTE_TOOLS_ENABLED=false
```

| 能力 | 说明 |
|------|------|
| ReadOnly / Execute 分离 | 巡检与变更权限拆分 |
| 默认关闭执行权限 | 管理员显式开启后才可修改 |
| Dangerous command filtering | 建连前拦截危险 SSH 命令 |
| Audit trail | Tool 调用可查询留痕 |

### 拦截示例

```
rm -rf /
   ↓
Blocked by security module
（不会发起远程 SSH）
```

详见：[docs/security.md](docs/security.md)

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

详见：[docs/architecture.md](docs/architecture.md)

---

## Screenshots

1. MCP Server Connection  
2. AI Infrastructure Health Check  
3. Docker Container Inspection  
4. MySQL Log Analysis  
5. SSH Security Filter  
6. Disk Cleanup Automation  

![MCP Server Connection](docs/screenshots/01-mcp-connection-tools.png)

![AI Infrastructure Health Check](docs/screenshots/02-server-health-check.png)

![Docker Container Inspection](docs/screenshots/03-docker-inspection.png)

![MySQL Log Analysis](docs/screenshots/04-mysql-log-analysis.png)

![SSH Security Filter](docs/screenshots/05-ssh-dangerous-command-filter.png)

![Disk Cleanup Automation](docs/screenshots/06-disk-cleanup-automation.png)

更多：[docs/screenshots/README.md](docs/screenshots/README.md)

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

将 `cwd` 设为 `YOUR_PROJECT_PATH`（勿提交真实路径）：

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

示例：[mcp_config_examples/cursor_mcp.json](mcp_config_examples/cursor_mcp.json)

### Test

```bash
pytest
```

### Docker

```bash
docker compose up -d --build
```

---

## Project Structure

```
enterprise-devops-mcp-server/
├── README.md / README_EN.md
├── CONTRIBUTING.md / CHANGELOG.md
├── LICENSE
├── app/                 # MCP Server + Tools + Security
├── docs/                # Architecture / Security / Screenshots
├── examples/            # MCP client examples
├── tests/               # 225+ pytest cases
└── .github/workflows/   # CI
```

---

## Contributing

见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## License

[MIT](LICENSE)

---

## Disclaimer

开启执行权限后，本软件可控制服务器与容器。请先在非生产环境验证。
