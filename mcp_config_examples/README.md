# MCP Client Configuration Examples

这些文件是 **公开示例**，请勿写入真实本机路径或生产主机信息。

## Placeholders

| Placeholder | Meaning |
|-------------|---------|
| `YOUR_PROJECT_PATH` | 本仓库在本地的绝对路径 |
| `YOUR_SERVER_IP` | 远程服务器地址（如需在文档中举例） |
| `YOUR_USERNAME` | SSH 用户名 |
| `YOUR_API_KEY` | API Key 占位（`.env.example`） |

## Files

| File | Client |
|------|--------|
| `cursor_mcp.json` | Cursor MCP |
| `claude_desktop.json` | Claude Desktop MCP |

## Security defaults in examples

- `ENABLE_SECURITY=true`
- `EXECUTE_TOOLS_ENABLED=false`
- `FASTMCP_SHOW_SERVER_BANNER=false`（避免横幅污染 MCP stdio）
