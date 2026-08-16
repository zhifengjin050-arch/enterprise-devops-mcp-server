# Enterprise Security Architecture

[中文](security.md) | [English](security.en.md)

> AI Agent 直接操作服务器存在风险。  
> 本项目通过 **Permission + Execute Protection + Command Filter + Audit**  
> 构建可治理的企业级访问路径。

---

## Security Principles

### 1. Least Privilege（最小权限）

默认：

```env
EXECUTE_TOOLS_ENABLED=false
```

含义：AI 可以巡检与查看；**不能**重启容器或执行远程变更，除非管理员显式开启。

### 2. Defense in Depth（纵深防御）

三层防护：

| Layer | 组件 | 作用 |
|-------|------|------|
| **Layer 1** | Permission | 模块白名单 + `READ_ONLY` / `EXECUTE` |
| **Layer 2** | Execute Protection | `OFF` / `BASIC` / `STRICT`（速率限制 / 确认） |
| **Layer 3** | Command Filter | SSH 危险命令黑名单，**建连前拦截** |

### 3. Auditability（可审计）

记录（实现字段以代码为准，对外可查询）：

- tool name
- arguments（敏感字段脱敏）
- permission result
- execution status
- duration
- timestamp

可通过 `get_audit_logs` 检索。

---

## Default Safe Mode

```env
ENABLE_SECURITY=true
EXECUTE_TOOLS_ENABLED=false
EXECUTE_PROTECTION_LEVEL=basic
```

| 配置 | 含义 |
|------|------|
| `EXECUTE_TOOLS_ENABLED=false` | **默认**：只读运维 |
| `EXECUTE_TOOLS_ENABLED=true` | 管理员授权后允许修改类操作 |
| `EXECUTE_PROTECTION_LEVEL=strict` | 速率限制 + 高危确认 |

---

## Real Case：Dangerous Command

**Input**

```text
rm -rf /
```

**Result**

```text
Blocked
```

**Remote execution**

```text
NO
```

系统行为：

1. 进入 `ssh_execute_command`
2. Dangerous Command Filter 命中黑名单
3. **阻止执行**
4. **不会发起任何 SSH 连接**
5. 写入审计记录

返回示例：

```json
{
  "stdout": "",
  "stderr": "命令包含危险操作 'rm -rf /'，已被安全模块拦截",
  "status": "1"
}
```

---

## Component Detail

### Permission Control

- 模块白名单：`system` / `docker` / `kubernetes` / `ssh`
- 操作分类：`READ_ONLY` vs `EXECUTE`
- 结构化拒绝原因

### Execute Protection

| 等级 | 行为 |
|------|------|
| `off` | 仅权限校验 |
| `basic` | 速率限制（默认） |
| `strict` | 速率限制 + 高危确认 |

### Dangerous Command Filter

示例黑名单片段：

```
rm -rf /
mkfs
dd if=
shutdown
reboot
:(){ :|:& };:
chmod -R 777 /
```

---

## Credential Handling

| Do | Don't |
|----|-------|
| Prefer SSH keys | Commit production passwords |
| Use `YOUR_SERVER_IP` / `YOUR_USERNAME` in docs | Commit real public IPs |
| Keep `.env` local | Commit tokens / private keys |

---

## Production Checklist

- [ ] Keep `EXECUTE_TOOLS_ENABLED=false` until needed
- [ ] Prefer `strict` in production execute mode
- [ ] Rotate any leaked credentials
- [ ] Least-privilege SSH users
- [ ] Review `get_audit_logs` regularly
