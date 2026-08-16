# 架构说明 · Enterprise Architecture

[中文](architecture.md) | [English](architecture.en.md)

## 概述

Enterprise DevOps MCP Server 基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)，  
把基础设施运维能力以 **Tool** 形式提供给 AI Agent，并在调用链中强制安全治理。

目标：**AI 可运维，但不可失控。**

---

## 总览架构

```
                 AI Agent
                    |
                    |
              MCP Protocol
                    |
                    |
        Enterprise DevOps MCP Server
                    |
 ------------------------------------------------
 |              |              |                |
System        Docker       Kubernetes        SSH

                    |
              Security Layer

        Permission
        Execute Protection
        Audit Logging
```

---

## Data Flow

```
User Request
      ↓
AI Agent
      ↓
MCP Tool Call
      ↓
Permission Validation
      ↓
Security Check
      ↓
Infrastructure Operation
      ↓
Audit Record
```

说明：

- **Permission Validation**：模块白名单 + READ / EXECUTE
- **Security Check**：执行开关、速率限制、危险命令过滤（SSH）
- **Infrastructure Operation**：仅在校验通过后触达本机 / 远程资源
- **Audit Record**：无论成功或拒绝，尽量留痕

---

## 安全横切层

```
┌─────────────────────────────────────┐
│  Enterprise DevOps MCP Server       │
│  (FastMCP)                          │
├─────────────────────────────────────┤
│  Security Layer                     │
│  ├── PermissionManager              │
│  ├── Execute Protection             │
│  ├── Dangerous Command Filter       │
│  └── AuditLogger                    │
└──────┬──────┬──────┬──────┬─────────┘
       │      │      │      │
       ▼      ▼      ▼      ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ System │ │ Docker │ │  K8s   │ │  SSH   │
   │ 监控   │ │ 容器   │ │ 集群   │ │ 远程   │
   └────────┘ └────────┘ └────────┘ └────────┘
```

---

## 分层职责

| 层级 | 职责 |
|------|------|
| **传输层** | stdio MCP（Cursor 等客户端拉起进程） |
| **工具层** | System / Docker / Kubernetes / SSH Tools（共 17） |
| **安全层** | 白名单、读写分离、危险命令过滤、速率限制 |
| **审计层** | 调用留痕（可查询） |
| **适配层** | psutil / Docker SDK / Kubernetes Client / paramiko |

---

## 工具分组

| 模块 | 能力 | 默认权限 |
|------|------|----------|
| System | 健康、资源、进程、审计查询 | 只读 |
| Docker | 列表、日志、重启 | 只读 + 执行(restart) |
| Kubernetes | Pod / Deployment / Service / Logs | 只读 |
| SSH | 连通性、命令、上传 | 只读 + 执行 |

---

## 企业级设计原则

1. **默认只读** — 巡检永远可用，修改需显式授权  
2. **执行需管理员开启** — `EXECUTE_TOOLS_ENABLED=true`  
3. **失败即关闭** — 危险命令在建连前拦截  
4. **统一策略与统一审计** — 本机与远程同一套治理  
5. **无强制数据库依赖** — V1 审计轻量部署  

---

## 企业使用场景

| 场景 | 示例对话 | 主要 Tool |
|------|----------|-----------|
| 值班巡检 | 「检查服务器是否健康」 | `get_server_health` |
| 容器排障 | 「分析 MySQL 最近错误」 | `docker_logs` |
| 远程诊断 | 「看一下远程磁盘」 | `ssh_execute_command` |
| 安全验收 | 「执行 rm -rf /」 | 过滤器拦截 |
| 合规回溯 | 「最近做了哪些操作」 | `get_audit_logs` |
