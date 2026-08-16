# Enterprise Security Architecture

[中文](security.md) | [English](security.en.md)

> Direct AI Agent access to servers is risky.  
> This project enforces **Permission + Execute Protection + Command Filter + Audit**.

---

## Security Principles

### 1. Least Privilege

Default:

```env
EXECUTE_TOOLS_ENABLED=false
```

### 2. Defense in Depth

| Layer | Component |
|-------|-----------|
| Layer 1 | Permission (`READ_ONLY` / `EXECUTE`) |
| Layer 2 | Execute Protection (`OFF` / `BASIC` / `STRICT`) |
| Layer 3 | Command Filter (block before SSH connect) |

### 3. Auditability

Records tool name, args (sensitive keys redacted), permission result, status, duration, timestamp.

---

## Real Case

**Dangerous command:** `rm -rf /`

**Result:** Blocked

**Remote execution:** NO

---

## Defaults

```env
ENABLE_SECURITY=true
EXECUTE_TOOLS_ENABLED=false
EXECUTE_PROTECTION_LEVEL=basic
```

Full Chinese detail: [security.md](security.md)
