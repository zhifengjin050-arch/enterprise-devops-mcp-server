# Demo pack — Enterprise DevOps MCP Server

默认只读：`EXECUTE_TOOLS_ENABLED=false`。不要提交 `.env`、kubeconfig、SSH 私钥。

## 3-minute path

```bash
git clone https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server.git
cd enterprise-devops-mcp-server
cp .env.example .env
pip install -r requirements.txt
python scripts/demo_list_tools.py
```

Windows:

```powershell
.\scripts\demo_start.ps1
```

Linux / macOS:

```bash
./scripts/demo_start.sh
```

Cursor MCP 示例：`mcp_config_examples/cursor_mcp.json`（路径写成 `YOUR_PROJECT_PATH`）。

## 面试时展示

1. 打印 17 个 Tool Schema 与风险等级
2. 说明危险命令拦截 + 只读闸门
3. `pytest`（CI 口径 225 passed）

## 截图

`python scripts/render_readme_images.py` 从 `docs/screenshots/html/` 导出，占位符为 `YOUR_SERVER_IP` / `YOUR_USERNAME`。
