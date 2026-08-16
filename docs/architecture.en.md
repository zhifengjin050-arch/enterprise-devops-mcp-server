# Architecture

[中文](architecture.md) | [English](architecture.en.md)

## Overview

Enterprise DevOps MCP Server exposes infrastructure operations as MCP **Tools** with a mandatory security layer.

Goal: **AI can operate, but cannot go out of control.**

---

## Architecture Diagram

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

---

## Layers

| Layer | Responsibility |
|-------|----------------|
| Transport | stdio MCP |
| Tools | System / Docker / Kubernetes / SSH (17 tools) |
| Security | whitelist, READ/EXECUTE, danger filter, rate limit |
| Audit | queryable call trail |
| Adapters | psutil / Docker SDK / Kubernetes Client / paramiko |

See also: [security.en.md](security.en.md)
