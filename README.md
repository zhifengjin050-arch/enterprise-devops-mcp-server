# Enterprise DevOps MCP Server

**中文** | [English](README_EN.md)

基于 **MCP（Model Context Protocol）** 的企业级 AI DevOps 运维自动化服务。

让 AI Agent（Cursor / Claude Desktop / 自研客户端）可以**安全调用**企业运维能力：

- Linux 服务器巡检
- Docker 容器管理
- SSH 远程执行
- Kubernetes 状态查询
- 日志分析工作流
- 可审计的安全控制

> 适合：**开源作品展示** · **简历 / 面试 Demo** · **AI Ops 实验**

---

## 为什么做这个项目？

多数 AI 编程助手只会**建议**你敲命令。  
本项目让 AI Agent 在受控规则下**真正调用运维工具**：

1. **读写分离**（READ / EXECUTE）
2. **危险命令过滤**
3. **速率限制与高危确认**
4. **内置审计日志**

一个 MCP Server 可同时管理**本机 Docker** 与**远程服务器**，策略统一、审计统一。

---

## 核心能力

### 服务器监控

| Tool | 说明 |
|------|------|
| `get_server_health` | CPU / 内存 / 磁盘 / 运行时长 / 健康等级 |
| `get_system_info` | 主机名 / OS / 平台 / Python / 运行时长 |
| `get_cpu_usage` | CPU 使用率 + 核心数 |
| `get_memory_usage` | 总量 / 已用 / 可用 / 百分比 |
| `get_disk_usage` | 各分区用量 |
| `list_processes` | 按 CPU Top N 进程 |
| `get_audit_logs` | 查询最近调用记录与统计 |

### Docker 管理

| Tool | 权限 |
|------|------|
| `docker_list` | 只读 |
| `docker_logs` | 只读 |
| `docker_restart` | 执行 |

### Kubernetes

| Tool | 权限 |
|------|------|
| `k8s_get_pods` | 只读 |
| `k8s_get_deployments` | 只读 |
| `k8s_get_services` | 只读 |
| `k8s_logs` | 只读 |

### SSH 自动化

| Tool | 权限 |
|------|------|
| `ssh_check_connection` | 只读 |
| `ssh_execute_command` | 执行 |
| `ssh_upload_file` | 执行 |

### 安全控制

- **执行权限管理**：写操作默认关闭
- **危险命令过滤**：拦截 `rm -rf /`、`mkfs`、`shutdown` 等
- **审计机制**：每次调用写入内存环形缓冲区

示例：AI 尝试通过 SSH 执行 `rm -rf /` → 在真正连远程前被拦截：

```json
{
  "stdout": "",
  "stderr": "命令包含危险操作 'rm -rf /'，已被安全模块拦截",
  "status": "1"
}
```

---

## 架构

```
Cursor / Claude / ChatGPT 客户端
              |
         MCP Client
              |
  Enterprise DevOps MCP Server
              |
   ---------------------------
   |           |             |
 System     Docker        SSH/K8s
 （本机）    （本机）       （远程）
```

详见：[架构说明](docs/architecture.md) · [安全设计](docs/security.md)  
English docs: [Architecture](docs/architecture.en.md) · [Security](docs/security.en.md)

---

## 环境要求

- Python **3.11+**
- Docker Desktop / Engine（Docker 工具需要）
- 可选：kubeconfig（Kubernetes 工具）
- 可选：可 SSH 连通的远程主机

---

## 安装

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

按需修改 `.env`。**切勿把 `.env` 提交到 Git。**

---

## 快速开始

### 1. 启动 MCP Server（stdio）

```bash
python -m app.server
# 或
python scripts/run_devops_mcp.py
```

### 2. 配置 Cursor MCP

将 [examples/mcp_config_example.json](examples/mcp_config_example.json) 复制到 Cursor 的 MCP 配置中。

最小示例：

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

> 把 `cwd` 改成你本机仓库的绝对路径，不要在公开文档里写私人路径。

### 3. 与 AI 对话体验

示例：

- `查看当前服务器健康状态`
- `列出正在运行的 Docker 容器`
- `查看 test-nginx 最近日志`
- `在远程主机执行 rm -rf /` → 应被**安全拦截**

---

## 安全设计（必读）

默认配置：

```env
EXECUTE_TOOLS_ENABLED=false
```

| 模式 | AI 能做什么 |
|------|-------------|
| 默认 | 仅巡检 / 查看 |
| `EXECUTE_TOOLS_ENABLED=true` | 可重启容器 / SSH 执行 / 上传 |
| `EXECUTE_PROTECTION_LEVEL=strict` | 速率限制 + 高危确认 |

生产建议：

1. 非必要不要打开执行权限
2. 优先使用 SSH 密钥，而不是密码
3. 切勿把生产密钥提交到 Git
4. 操作后用 `get_audit_logs` 复查

完整说明：[docs/security.md](docs/security.md)

---

## 截图

| # | 场景 |
|---|------|
| 01 | MCP 连接与 Tool 发现 |
| 02 | AI 服务器健康巡检 |
| 03 | Docker 容器巡检 |
| 04 | MySQL 日志分析 |
| 05 | SSH 危险命令安全过滤 |
| 06 | 磁盘清理自动化 |

![01 MCP 连接](docs/screenshots/01-mcp-connection-tools.png)

![02 健康巡检](docs/screenshots/02-server-health-check.png)

![03 Docker 巡检](docs/screenshots/03-docker-inspection.png)

![04 MySQL 日志](docs/screenshots/04-mysql-log-analysis.png)

![05 SSH 拦截](docs/screenshots/05-ssh-dangerous-command-filter.png)

![06 磁盘清理](docs/screenshots/06-disk-cleanup-automation.png)

---

## 项目结构

```
enterprise-devops-mcp-server/
├── README.md              # 中文（默认）
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

## 测试

```bash
python -m pytest tests/ -v
```

预期：**225+** 测试通过。

```bash
docker compose --profile test run --rm mcp-server-test
```

---

## 环境变量摘要

| 变量 | 默认值 | 含义 |
|------|--------|------|
| `ENABLE_SECURITY` | `true` | 安全总开关 |
| `EXECUTE_TOOLS_ENABLED` | `false` | 是否允许执行类工具 |
| `ALLOWED_TOOLS` | `system,docker,kubernetes,ssh` | 模块白名单 |
| `EXECUTE_PROTECTION_LEVEL` | `basic` | `off` / `basic` / `strict` |
| `AUDIT_LOG_ENABLED` | `true` | 是否启用审计 |
| `SSH_SERVERS` | 空 | 多主机注册（不要存密码） |

---

## 路线图

| 版本 | 重点 |
|------|------|
| **V1.0** | 本地 MCP + System/Docker/K8s/SSH + 安全 + 测试 |
| **V1.1** | HTTP/SSE 传输 + 身份认证 + RBAC |
| 后续 | 审计导出、多租户策略包 |

---

## 贡献

1. Fork 并创建功能分支
2. 保持安全默认值保守
3. 补充 / 调整测试
4. 不要提交 `.env`、密钥或真实基础设施标识

---

## License

[MIT](LICENSE)

---

## 免责声明

开启执行权限后，本软件可控制服务器与容器。  
请自行承担风险，务必先在非生产环境验证。  
作者不对滥用或误操作造成的损失负责。
