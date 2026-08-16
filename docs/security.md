# Security Design

Enterprise DevOps MCP Server is built for **AI Agent access under human-controlled guardrails**.

## Default Safe Mode

```env
ENABLE_SECURITY=true
EXECUTE_TOOLS_ENABLED=false
EXECUTE_PROTECTION_LEVEL=basic
```

With these defaults:

- AI can inspect (health, docker list/logs, k8s status, SSH connectivity)
- AI **cannot** restart containers or run remote commands
- Rate limits apply when execute mode is later enabled

## Three Security Layers

### 1. Permission Control

- Module whitelist: `system`, `docker`, `kubernetes`, `ssh`
- Operation classification: `READ` vs `EXECUTE`
- Structured deny reasons for agents and humans

### 2. Execute Protection

| Level | Behavior |
|-------|----------|
| `off` | Permission checks only |
| `basic` | Rate limit (default 10 calls/min) |
| `strict` | Rate limit + high-risk confirmation |

### 3. Audit Logging

Every tool call records:

- timestamp
- tool name
- arguments (sensitive keys redacted in permission layer)
- permission result
- execution status
- duration

Query via MCP tool: `get_audit_logs`

## Dangerous Command Filter (SSH)

Even when execute mode is enabled, commands matching the blacklist are blocked
**before** any SSH session is opened. Examples:

```
rm -rf /
mkfs
dd if=
shutdown
reboot
:(){ :|:& };:
chmod -R 777 /
```

Example response:

```json
{
  "stdout": "",
  "stderr": "命令包含危险操作 'rm -rf /'，已被安全模块拦截",
  "status": "1"
}
```

## Credential Handling

| Do | Don't |
|----|-------|
| Use SSH keys | Put production passwords in `.env` |
| Use `YOUR_SERVER_IP` placeholders in docs | Commit real cloud IPs |
| Pass password only at call-time if unavoidable | Commit API tokens / private keys |
| Keep `.env` local (gitignored) | Share screenshots with real host fields |

## Production Checklist

- [ ] `EXECUTE_TOOLS_ENABLED=false` until needed
- [ ] Prefer `strict` protection for production execute mode
- [ ] Rotate any credentials that ever appeared in chat/screenshots
- [ ] Restrict SSH user privileges on remote hosts
- [ ] Review `get_audit_logs` regularly
