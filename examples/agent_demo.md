# AI Agent 调用示例

本文档演示 AI Agent（如 Cursor、Claude Desktop、自研 Agent）如何通过 MCP 协议与 Enterprise DevOps MCP Server 交互。

---

## 场景 1：服务器状态检查

**用户请求：**
> 帮我检查一下当前服务器的运行状态。

**Agent 调用：**
```
Tool: get_server_health
参数: (无)
```

**返回结果：**
```json
{
  "hostname": "server01",
  "cpu_usage": 23.5,
  "memory_usage": 61.2,
  "disk_usage": 40.1,
  "uptime": "10 days, 3 hours, 25 minutes",
  "status": "healthy"
}
```

**Agent 回复：**
> 服务器运行正常。CPU 使用率 23.5%、内存 61.2%、磁盘 40.1%，所有指标均在健康范围内（< 80%），系统已运行 10 天 3 小时。

---

## 场景 2：查看 Docker 容器状态

**用户请求：**
> 看看现在 Docker 上跑了哪些服务。

**Agent 调用：**
```
Tool: docker_list
参数: {"all_containers": false}
```

**返回结果：**
```json
[
  {
    "name": "nginx",
    "image": "nginx:latest",
    "status": "running",
    "ports": "80:80/tcp, 443:443/tcp"
  },
  {
    "name": "redis",
    "image": "redis:7",
    "status": "running",
    "ports": "6379:6379/tcp"
  },
  {
    "name": "postgres",
    "image": "postgres:15",
    "status": "running",
    "ports": "5432:5432/tcp"
  }
]
```

**Agent 回复：**
> 当前运行了 3 个容器：Nginx（Web 服务，端口 80/443）、Redis（缓存，端口 6379）、PostgreSQL（数据库，端口 5432），全部正常运行。

---

## 场景 3：分析容器异常

**用户请求：**
> nginx 服务好像有问题，帮我看看日志。

**Agent 调用：**
```
Tool: docker_logs
参数: {"container_name": "nginx", "lines": 50}
```

**返回结果：**
```json
{
  "container": "nginx",
  "logs": "2024/01/15 10:23:45 [error] connect() failed (111: Connection refused)\n2024/01/15 10:23:46 [error] upstream timed out (110: Connection timed out)\n..."
}
```

**Agent 回复：**
> 从 nginx 日志中发现后端 upstream 连接被拒绝和超时错误，可能是后端服务故障。建议检查后端服务状态或查看数据库/应用容器日志。

---

## 场景 4：重启容器（需权限）

**用户请求：**
> 把 nginx 重启一下。

**Agent 流程：**

```
步骤 1: Agent 检查权限配置
步骤 2: Agent 发起调用
```

**Agent 调用：**
```
Tool: docker_restart
参数: {"container_name": "nginx"}
```

**情况 A — 权限已开启：**
```json
{
  "container": "nginx",
  "action": "restart",
  "status": "success"
}
```

**情况 B — 权限未开启：**
```json
{
  "error": "execute_permission_denied",
  "message": "Tool 'docker_restart' 需要执行权限，请管理员设置 EXECUTE_TOOLS_ENABLED=true"
}
```

**Agent 回复：**
> 情况 A：nginx 容器已成功重启。
> 情况 B：重启操作需要管理员权限，请在 .env 中将 EXECUTE_TOOLS_ENABLED 设置为 true 后再试。

---

## 完整调用流程

```
┌─────────────────────────────────────────────────┐
│  用户发送自然语言请求                             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  AI Agent（Cursor / Claude / 自研 Agent）        │
│  1. 理解用户意图                                 │
│  2. 判断需要调用的 MCP Tool                      │
│  3. 检查 Tool 权限                               │
│  4. 构造 Tool 参数                               │
└──────────────────┬──────────────────────────────┘
                   │ MCP Protocol
                   ▼
┌─────────────────────────────────────────────────┐
│  Enterprise DevOps MCP Server                   │
│  1. 接收 Tool 调用请求                           │
│  2. PermissionManager 权限校验                   │
│  3. 执行 Tool 逻辑                               │
│  4. 返回结构化结果                               │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  AI Agent 解析结果，生成自然语言回复给用户         │
└─────────────────────────────────────────────────┘
```