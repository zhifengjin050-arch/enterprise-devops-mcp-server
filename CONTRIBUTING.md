# Contributing

感谢你对 **Enterprise DevOps MCP Server** 的关注。欢迎提交 Issue 与 Pull Request。

当前发布基线：**v1.0.1** · **230 tests passed** · **18 MCP Tools** · Enterprise Security Architecture。

行为准则：[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。安全披露：[SECURITY.md](SECURITY.md)。

---

## 开发环境

要求：

- Python 3.11+
-（可选）Docker Desktop / Docker Engine
-（可选）可访问的 Kubernetes 集群（不强制，单元测试可 mock）

```bash
git clone https://github.com/zhifengjin050-arch/enterprise-devops-mcp-server.git
cd enterprise-devops-mcp-server

python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

安全默认值请保持：

```env
EXECUTE_TOOLS_ENABLED=false
```

---

## 测试方式

```bash
pytest
```

或：

```bash
python -m pytest tests/ -v
```

提交前请确保本地测试通过（当前发布基线：**230+ passed**）。

Docker 测试 profile：

```bash
docker compose --profile testing run --rm mcp-server-test
```

---

## 代码规范

1. **不要降低安全默认策略**（尤其是 `EXECUTE_TOOLS_ENABLED=false`）
2. **不要在仓库中提交** `.env`、密钥、真实 IP、真实密码、Token
3. 文档与示例统一使用占位符：
   - `YOUR_PROJECT_PATH`
   - `YOUR_SERVER_IP`
   - `YOUR_USERNAME`
   - `YOUR_API_KEY`
4. 新增 Tool 时同步补充测试与 README / docs 说明
5. 保持变更聚焦：优先小而清晰的 PR

---

## Pull Request 流程

1. Fork 本仓库并创建功能分支  
2. 完成改动并运行 `pytest`  
3. 更新相关文档（如行为或配置有变）  
4. 发起 Pull Request，说明：
   - 变更动机
   - 测试结果
   - 是否影响安全默认值
5. Maintainer Review 通过后合并

---

## 安全相关贡献

若发现安全问题：

- 请勿在公开 Issue 中粘贴真实凭证或可利用细节
- 优先通过私密渠道联系 Maintainer，或先开 Issue 描述影响面（不含敏感信息）

---

## License

贡献代码默认遵循本仓库 [MIT License](LICENSE)。
