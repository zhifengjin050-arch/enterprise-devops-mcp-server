# Enterprise DevOps MCP Server

**中文** | [English](README_EN.md)

> **V1.0.1** · MIT · [Architecture](docs/architecture.md) · [Security](docs/security.md) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

---

## 项目定位

**Enterprise AI DevOps MCP Server enables AI Agents to securely operate infrastructure through MCP protocol.**

基于 **MCP（Model Context Protocol）** 协议构建企业级 AI 运维 Agent 服务，  
让 AI Agent 在安全控制范围内管理 Linux、Docker、Kubernetes 和 SSH 基础设施。

---

## Why This Project

### 传统方式

```
Engineer
   ↓
  SSH
   ↓
Manual Command
```

权限大、难审计、难规模化；AI 通常只能“建议命令”，人还要自己敲。

### AI DevOps（本项目）

```
AI Agent
   ↓
MCP Protocol
   ↓
Security Layer
   ↓
Infrastructure
```

**关键点：AI 不直接拥有服务器权限。**

所有操作必须经过：

1. **Permission Control**
2. **Execute Protection**
3. **Command Filtering**
4. **Audit Logging**

---

## Features

### Infrastructure Management

✅ **Linux monitoring**

- CPU
- Memory
- Disk
- Process
- Health assessment / Audit query

✅ **Docker**

- Container listing
- Container logs
- Container restart（EXECUTE，默认关闭）

✅ **Kubernetes**

- Pods
- Deployments
- Services
- Logs

✅ **SSH**

- Connection check
- Remote command execution（EXECUTE，默认关闭）
- Secure file upload（EXECUTE，默认关闭）

**MCP Tools：17**（System 7 · Docker 3 · Kubernetes 4 · SSH 3）

### Enterprise Security

✅ **Permission Control** — `READ_ONLY` / `EXECUTE`

✅ **Execute Protection** — `OFF` / `BASIC` / `STRICT`

✅ **Dangerous Command Filter**

```
rm -rf /
   ↓
Blocked before remote execution
```

✅ **Audit Logging** — 可查询调用留痕

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
        Permission / Execute Protection / Audit
```

完整说明：[docs/architecture.md](docs/architecture.md)

---

## Screenshots

1. MCP Server Connection  
2. AI Infrastructure Health Check  
3. Docker Container Inspection  
4. MySQL Log Analysis  
5. SSH Security Filter  
6. Disk Cleanup Automation  

![1. MCP Server Connection](docs/screenshots/01-mcp-connection-tools.png)

![2. AI Infrastructure Health Check](docs/screenshots/02-server-health-check.png)

![3. Docker Container Inspection](docs/screenshots/03-docker-inspection.png)

![4. MySQL Log Analysis](docs/screenshots/04-mysql-log-analysis.png)

![5. SSH Security Filter](docs/screenshots/05-ssh-dangerous-command-filter.png)

![6. Disk Cleanup Automation](docs/screenshots/06-disk-cleanup-automation.png)

索引：[docs/screenshots/README.md](docs/screenshots/README.md)

---

## Quick Start

### Clone

```bash
git clone https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server.git
cd enterprise-devops-mcp-server
```

### Install

```bash
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

默认安全策略：`EXECUTE_TOOLS_ENABLED=false`（只读运维）。

### Start

```bash
python -m app.server
```

### Test

```bash
pytest
```

### Docker

```bash
docker compose up -d --build
docker compose --profile testing run --rm mcp-server-test
```

---

## Cursor MCP 配置

参考 [`mcp_config_examples/cursor_mcp.json`](mcp_config_examples/cursor_mcp.json)。

将 `YOUR_PROJECT_PATH` 替换为本地项目绝对路径（**不要提交真实路径**）：

```json
{
  "mcpServers": {
    "enterprise-devops": {
      "command": "python",
      "args": ["scripts/run_devops_mcp.py"],
      "cwd": "YOUR_PROJECT_PATH",
      "env": {
        "FASTMCP_SHOW_SERVER_BANNER": "false",
        "ENABLE_SECURITY": "true",
        "EXECUTE_TOOLS_ENABLED": "false"
      }
    }
  }
}
```

---

## Project Structure

```
enterprise-devops-mcp-server/
├── README.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── app/
├── docs/
├── examples/
├── mcp_config_examples/
├── scripts/
└── tests/
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
