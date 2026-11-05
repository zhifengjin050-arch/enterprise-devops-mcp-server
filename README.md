<div align="center">

# Enterprise DevOps MCP Server

**MCP server for governed AI Agent tool calling over Linux, Docker, Kubernetes, and SSH.**

让 AI Agent 在安全边界内做基础设施自动化——而不是拿到不受限的 shell。

[English](README_EN.md) · [Architecture](docs/architecture.md) · [Security](SECURITY.md) · [Contributing](CONTRIBUTING.md)

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()
[![Tests](https://img.shields.io/badge/tests-230%20passed-brightgreen)](https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server/actions)
[![MCP](https://img.shields.io/badge/MCP-18_tools-8A2BE2)]()
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

<!-- engineering-guide:start -->
## 🧭 工程导读 · 从场景到实现

**具有执行边界的运维工具层**。将 Linux、Docker、Kubernetes 和 SSH 操作封装为 MCP 工具，使客户端可以发现工具，并理解其权限与风险。

```mermaid
flowchart LR
  N0["MCP 客户端"]
  N1["工具元数据"]
  N2["权限与执行门"]
  N3["基础设施操作"]
  N4["审计记录"]
  N0 --> N1 --> N2 --> N3 --> N4
```

- 工具目录同时描述类别、风险和所需权限，便于客户端选择工具及开发者审查能力。
- EXECUTE_TOOLS_ENABLED 默认关闭；模块许可、参数或命令检查与审计需要结合实际入口阅读。
- 协议接入和底层执行分离：先验证工具枚举，再逐步接入容器、集群或 SSH 环境。

📖 **[阅读完整工程导读](docs/PROJECT_GUIDE.md)**：源码路径、最短运行路线、演示验收与当前边界。
<!-- engineering-guide:end -->



> **AI Agent → MCP Protocol → Security Layer → Infrastructure**

---

## Positioning

Enterprise AIOps building block: Cursor / Claude / any MCP client calls **18 tools** through module whitelist, execute protection, command filtering, and audit logging.

Default posture: **read-only** (`EXECUTE_TOOLS_ENABLED=false`).

---

## Demo

[![Demo video](docs/videos/cover.png)](https://zhifengjin050-arch.github.io/enterprise-devops-mcp-server/)

点击封面在线播放（中文旁白 + 底部字幕）。GitHub 文件页无法内嵌 mp4，演示页托管在 GitHub Pages。

---

## Features

| Feature | Status |
|---------|--------|
| Linux monitoring | ✅ |
| Docker management | ✅ |
| Kubernetes read APIs | ✅ |
| SSH automation | ✅ |
| Permission control | ✅ |
| Execute protection | ✅ |
| Audit logging | ✅ |
| Docker Compose deploy | ✅ |
| GitHub Actions CI | ✅ |

---

## MCP tool catalog

| Tool | Category | Risk | Permission |
|------|----------|------|------------|
| `get_server_health` | system | safe | viewer |
| `get_system_info` | system | safe | viewer |
| `get_cpu_usage` | system | safe | viewer |
| `get_memory_usage` | system | safe | viewer |
| `get_disk_usage` | system | safe | viewer |
| `list_processes` | system | safe | viewer |
| `confirm_execute_action` | system | moderate | viewer |
| `get_audit_logs` | system | moderate | admin |
| `docker_list` | docker | safe | viewer |
| `docker_logs` | docker | safe | viewer |
| `docker_restart` | docker | dangerous | admin |
| `k8s_get_pods` | kubernetes | safe | viewer |
| `k8s_get_deployments` | kubernetes | safe | viewer |
| `k8s_get_services` | kubernetes | safe | viewer |
| `k8s_logs` | kubernetes | safe | viewer |
| `ssh_check_connection` | ssh | safe | viewer |
| `ssh_execute_command` | ssh | dangerous | admin |
| `ssh_upload_file` | ssh | dangerous | admin |

---

## Architecture

<img src="docs/images/architecture.png" alt="MCP architecture" width="100%" />

```mermaid
flowchart TB
    Client[Cursor / Claude / AI Agent]
    Client --> MCP[MCP Protocol]
    MCP --> Server[Enterprise DevOps MCP Server]
    Server --> Sec[Security Layer]
    Sec --> Sys[Linux]
    Sec --> Dock[Docker]
    Sec --> K8s[Kubernetes]
    Sec --> SSH[SSH]
    subgraph sec [Controls]
      P[Module ACL]
      E[Execute gate]
      F[Command filter]
      A[Audit log]
    end
    Server -.-> P
```

---

## Screenshots

| MCP tools | Cursor / Claude |
|-----------|-----------------|
| ![Tools](docs/images/mcp-tools.png) | ![Cursor MCP](docs/images/cursor-claude-mcp.png) |

| Architecture |
|--------------|
| ![Architecture](docs/images/architecture.png) |

Cursor / Claude 图为 **Product Preview**（能力示意）。将本仓库配置进 MCP 后即可在 IDE 中真实调用。

---

## Quick Start

```bash
git clone https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server.git
cd enterprise-devops-mcp-server
cp .env.example .env
pip install -r requirements.txt
python scripts/demo_list_tools.py
./scripts/demo_start.sh          # Windows: .\scripts\demo_start.ps1
```

Keep `EXECUTE_TOOLS_ENABLED=false`. See [demo/README.md](demo/README.md). Do not commit `.env`, kubeconfig, or SSH keys.

### Docker

```bash
docker compose up -d --build
```

### Cursor MCP

```json
{
  "mcpServers": {
    "enterprise-devops": {
      "command": "python",
      "args": ["scripts/run_devops_mcp.py"],
      "cwd": "YOUR_PROJECT_PATH",
      "env": {
        "EXECUTE_TOOLS_ENABLED": "false"
      }
    }
  }
}
```

Example: [mcp_config_examples/cursor_mcp.json](mcp_config_examples/cursor_mcp.json)

```bash
pytest
```

---

## Deployment

| Mode | Command |
|------|---------|
| Local | `python -m app.server` |
| Docker | `docker compose up -d --build` |

Never enable execute tools in production without an explicit change-control process.

---

## Roadmap

**v1.0.x (current):** 18 tools, security layer, audit, Docker, CI.

Later: more cloud providers, finer-grained policy packs, signed audit export.

---

## License

[MIT](LICENSE)

[CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) · [SECURITY.md](SECURITY.md) · [CHANGELOG.md](CHANGELOG.md)

**Disclaimer:** with execute enabled, this software can change hosts and containers. Validate in non-production first.
