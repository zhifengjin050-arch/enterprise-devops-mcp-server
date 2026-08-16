# 架构说明

[中文](architecture.md) | [English](architecture.en.md)

## 概述

Enterprise DevOps MCP Server 通过 [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)  
将运维能力暴露给 AI Agent。

```
┌─────────────────────────────────────┐
│  AI 客户端                          │
│  Cursor / Claude Desktop / 自研     │
└──────────────────┬──────────────────┘
                   │ MCP Protocol (stdio)
                   ▼
┌─────────────────────────────────────┐
│  Enterprise DevOps MCP Server       │
│  (FastMCP)                          │
├─────────────────────────────────────┤
│  安全层                             │
│  ├── 权限控制                       │
│  ├── 执行保护                       │
│  └── 审计日志                       │
└──────┬──────┬──────┬──────┬─────────┘
       │      │      │      │
       ▼      ▼      ▼      ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ System │ │ Docker │ │  K8s   │ │  SSH   │
   │ 监控   │ │ 容器   │ │ 集群   │ │ 远程   │
   └────────┘ └────────┘ └────────┘ └────────┘
```

## 分层职责

| 层级 | 职责 |
|------|------|
| **传输层** | stdio MCP（由 Cursor 启动进程） |
| **工具注册** | System / Docker / K8s / SSH 的 FastMCP Tools |
| **安全层** | 白名单、读写分离、速率限制、确认机制 |
| **审计层** | 内存环形缓冲记录每次调用 |
| **适配层** | psutil / Docker SDK / Kubernetes client / paramiko |

## 工具分组

| 模块 | 工具 | 默认权限 |
|------|------|----------|
| System | health / info / cpu / memory / disk / processes / audit | 只读 |
| Docker | list / logs / restart | 只读 + 执行(restart) |
| Kubernetes | pods / deployments / services / logs | 只读 |
| SSH | check / execute / upload | 只读 + 执行 |

## 设计原则

1. **默认只读** — 巡检类工具始终可用  
2. **执行需显式开启** — 写操作要求 `EXECUTE_TOOLS_ENABLED=true`  
3. **失败即关闭** — 危险 SSH 命令在建连前拦截  
4. **无数据库依赖** — V1 审计仅使用内存  
5. **一个 Server 管全部** — 本机 Docker + 远程 SSH/K8s 统一策略与审计  
