# Architecture

## Overview

Enterprise DevOps MCP Server exposes DevOps capabilities to AI Agents through the
[Model Context Protocol (MCP)](https://modelcontextprotocol.io/).

```
┌─────────────────────────────────────┐
│  AI Client                          │
│  Cursor / Claude Desktop / Custom   │
└──────────────────┬──────────────────┘
                   │ MCP Protocol (stdio)
                   ▼
┌─────────────────────────────────────┐
│  Enterprise DevOps MCP Server       │
│  (FastMCP)                          │
├─────────────────────────────────────┤
│  Security Layer                     │
│  ├── Permission Control             │
│  ├── Execute Protection             │
│  └── Audit Logging                  │
└──────┬──────┬──────┬──────┬─────────┘
       │      │      │      │
       ▼      ▼      ▼      ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │ System │ │ Docker │ │  K8s   │ │  SSH   │
   │Monitor │ │Containers│ │Cluster│ │ Remote │
   └────────┘ └────────┘ └────────┘ └────────┘
```

## Layers

| Layer | Responsibility |
|-------|----------------|
| **Transport** | stdio MCP (Cursor starts the process) |
| **Tool Registry** | FastMCP tools for System / Docker / K8s / SSH |
| **Security** | Whitelist, READ vs EXECUTE, rate limit, confirmation |
| **Audit** | In-memory ring buffer of every tool call |
| **Adapters** | psutil / Docker SDK / Kubernetes client / paramiko |

## Tool Groups

| Module | Tools | Default Access |
|--------|-------|----------------|
| System | health, info, cpu, memory, disk, processes, audit logs | READ |
| Docker | list, logs, restart | READ + EXECUTE(restart) |
| Kubernetes | pods, deployments, services, logs | READ |
| SSH | check, execute, upload | READ + EXECUTE |

## Design Principles

1. **Read by default** — inspection tools always available
2. **Execute opt-in** — write operations require `EXECUTE_TOOLS_ENABLED=true`
3. **Fail closed** — dangerous SSH commands are blocked before connection
4. **No database required** — audit stays in memory for V1
5. **One server, many targets** — local Docker + remote SSH/K8s in one MCP
