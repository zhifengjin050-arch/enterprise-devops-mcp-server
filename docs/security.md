# 安全设计

[中文](security.md) | [English](security.en.md)

Enterprise DevOps MCP Server 面向「**人类可控护栏下的 AI Agent 访问**」而设计。

## 默认安全模式

```env
ENABLE_SECURITY=true
EXECUTE_TOOLS_ENABLED=false
EXECUTE_PROTECTION_LEVEL=basic
```

在此默认下：

- AI 可以巡检（健康、Docker 列表/日志、K8s 状态、SSH 连通性）
- AI **不能**重启容器或执行远程命令
- 后续开启执行模式时，仍会生效速率限制

## 三层安全体系

### 1. 权限控制

- 模块白名单：`system`、`docker`、`kubernetes`、`ssh`
- 操作分类：`READ` vs `EXECUTE`
- 结构化拒绝原因，便于 Agent 与人工理解

### 2. 执行保护

| 等级 | 行为 |
|------|------|
| `off` | 仅权限校验 |
| `basic` | 速率限制（默认 10 次/分钟） |
| `strict` | 速率限制 + 高危确认 |

### 3. 审计日志

每次 Tool 调用记录：

- 时间戳
- 工具名
- 参数（权限层会对敏感字段脱敏）
- 权限结果
- 执行状态
- 耗时

可通过 MCP Tool 查询：`get_audit_logs`

## 危险命令过滤（SSH）

即使开启了执行模式，命中黑名单的命令也会在**建立任何 SSH 会话之前**被拦截。例如：

```
rm -rf /
mkfs
dd if=
shutdown
reboot
:(){ :|:& };:
chmod -R 777 /
```

示例返回：

```json
{
  "stdout": "",
  "stderr": "命令包含危险操作 'rm -rf /'，已被安全模块拦截",
  "status": "1"
}
```

## 凭证处理

| 建议 | 禁止 |
|------|------|
| 使用 SSH 密钥 | 把生产密码写进 `.env` |
| 文档使用 `YOUR_SERVER_IP` 占位 | 提交真实云服务器 IP |
| 必要时仅在调用时传入密码 | 提交 API Token / 私钥 |
| `.env` 仅本地保存（已 gitignore） | 截图中暴露真实主机信息 |

## 生产检查清单

- [ ] 非必要保持 `EXECUTE_TOOLS_ENABLED=false`
- [ ] 生产执行模式优先使用 `strict`
- [ ] 轮换曾出现在聊天/截图中的任何凭证
- [ ] 限制远程主机上的 SSH 用户权限
- [ ] 定期查看 `get_audit_logs`
