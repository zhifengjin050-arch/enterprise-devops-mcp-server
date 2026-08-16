# Enterprise DevOps MCP Server — 完整演示流程

> 展示 AI Agent 如何通过 MCP 协议完成一次完整的 DevOps 故障排查与修复闭环。

---

## 场景：Web 服务宕机

假设某 Web 服务宕机，AI Agent 需要：

1. **检查服务器状态** → 发现异常
2. **查看 Docker 日志** → 发现应用错误
3. **查询 K8s Pod 状态** → 确认 Pod 异常
4. **SSH 远程修复** → 执行修复命令

---

## 步骤 1：检查服务器状态

**用户请求：**

> 检查一下服务器整体状态

**AI 调用：** `get_server_health`

```json
// 请求
{
  "tool": "get_server_health"
}

// 返回
{
  "hostname": "prod-web-01",
  "cpu_usage_percent": 95.2,
  "memory_usage_percent": 87.3,
  "disk_usage_percent": 72.1,
  "uptime": "15 days, 3 hours, 22 minutes",
  "status": "warning"
}
```

**AI 推理：** CPU 使用率 95%、内存 87%，服务器负载过高。需要进一步排查容器和 Pod 状态。

---

## 步骤 2：查看 Docker 容器日志

**用户请求：**

> 看看 Nginx 容器的日志

**AI 调用：** `docker_logs`

```json
// 请求
{
  "tool": "docker_logs",
  "arguments": {
    "container_name": "nginx-proxy",
    "lines": 50
  }
}

// 返回
{
  "container": "nginx-proxy",
  "logs": "2026/08/16 10:23:45 [error] connect() failed (111: Connection refused)..."
}
```

**AI 推理：** Nginx 无法连接到后端服务，怀疑后端 K8s Pod 异常。

---

## 步骤 3：查询 K8s Pod 状态

**用户请求：**

> 检查 default 命名空间的 Pod

**AI 调用：** `k8s_get_pods`

```json
// 请求
{
  "tool": "k8s_get_pods",
  "arguments": {
    "namespace": "default"
  }
}

// 返回
[
  {
    "name": "web-app-7d8f9c2b4-x3k9m",
    "namespace": "default",
    "status": "CrashLoopBackOff",
    "ready": "0/1",
    "restarts": "5",
    "node": "worker-2"
  },
  {
    "name": "nginx-proxy-6a2b3c4d5-p7q8r",
    "namespace": "default",
    "status": "Running",
    "ready": "1/1",
    "restarts": "0",
    "node": "worker-1"
  }
]
```

**AI 推理：** `web-app` Pod 处于 `CrashLoopBackOff` 状态，重启了 5 次。需要查看日志了解原因。

---

## 步骤 4：查看 K8s Pod 日志

**用户请求：**

> 查看 web-app Pod 的日志

**AI 调用：** `k8s_logs`

```json
// 请求
{
  "tool": "k8s_logs",
  "arguments": {
    "pod_name": "web-app-7d8f9c2b4-x3k9m",
    "namespace": "default",
    "lines": 100
  }
}

// 返回
{
  "pod": "web-app-7d8f9c2b4-x3k9m",
  "namespace": "default",
  "logs": "Error:无法连接到数据库 127.0.0.1:3306\nConnection refused\n..."
}
```

**AI 推理：** 应用无法连接数据库。需要检查数据库配置和数据库服务状态。

---

## 步骤 5：SSH 远程排查

**用户请求：**

> SSH 连接到 worker-2，检查 mysql 服务状态

**AI 调用：** `ssh_execute_command`

> 注意：此操作需要管理员开启 `EXECUTE_TOOLS_ENABLED=true`

```json
// 请求
{
  "tool": "ssh_execute_command",
  "arguments": {
    "host": "YOUR_SERVER_IP",
    "username": "admin",
    "command": "systemctl status mysql"
  }
}

// 返回
{
  "stdout": "● mysql.service - MySQL Community Server\n   Loaded: loaded\n   Active: inactive (dead)",
  "stderr": "",
  "status": "0"
}
```

**AI 推理：** MySQL 服务已停止。

---

## 步骤 6：SSH 远程修复

**用户请求：**

> 启动 MySQL 服务

**AI 调用：** `ssh_execute_command`

```json
// 请求
{
  "tool": "ssh_execute_command",
  "arguments": {
    "host": "YOUR_SERVER_IP",
    "username": "admin",
    "command": "systemctl start mysql"
  }
}

// 返回
{
  "stdout": "",
  "stderr": "",
  "status": "0"
}
```

---

## 步骤 7：验证修复结果

**用户请求：**

> 再次检查 web-app Pod 状态

**AI 调用：** `k8s_get_pods`

```json
// 返回
[
  {
    "name": "web-app-7d8f9c2b4-x3k9m",
    "namespace": "default",
    "status": "Running",
    "ready": "1/1",
    "restarts": "5",
    "node": "worker-2"
  }
]
```

**AI 推理：** Pod 已恢复正常运行状态。数据库启动后，应用成功连接数据库。

---

## 完整调用链总结

```
用户请求
    │
    ▼
AI Agent 自动编排
    │
    ├── 1. get_server_health     → 发现服务器负载过高
    ├── 2. docker_logs           → 发现 Nginx 无法连接后端
    ├── 3. k8s_get_pods          → 发现 web-app CrashLoopBackOff
    ├── 4. k8s_logs              → 发现无法连接数据库
    ├── 5. ssh_execute_command   → 发现 MySQL 服务停止
    ├── 6. ssh_execute_command   → 启动 MySQL 服务
    └── 7. k8s_get_pods          → 确认 Pod 恢复 Running
```

**无需人工介入** — AI Agent 完成全链路排查与修复。

---

## 关键安全点

| 步骤 | 安全措施 |
|------|----------|
| get_server_health | READ_ONLY，直接放行 |
| docker_logs | READ_ONLY，直接放行 |
| k8s_get_pods | READ_ONLY，直接放行 |
| k8s_logs | READ_ONLY，直接放行 |
| ssh_execute_command | **EXECUTE**，需要 `EXECUTE_TOOLS_ENABLED=true` |
| | 危险命令过滤（禁止 rm -rf /, shutdown, reboot） |
| | 速率限制（默认 10 次/分钟） |
| | 审计日志记录 |

---

## 一键演示

使用 `docker compose up` 启动后，AI Agent 即可通过 MCP Client（Cursor / Claude Desktop）自动发现所有 Tool。

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env

# 3. 启动服务
python -m app.server

# 4. 在 Cursor / Claude Desktop 中开始对话
# "检查服务器状态" → "查看 Docker 日志" → "查询 K8s Pod"
```