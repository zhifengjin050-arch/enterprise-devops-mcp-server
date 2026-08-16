# ------------------------------------------------------------
# Enterprise DevOps MCP Server - Docker 镜像
# ------------------------------------------------------------
# 多阶段构建：更大体积生产镜像 vs 最小体积开发镜像
# ------------------------------------------------------------

# ---- Stage 1: 基础依赖 ----
FROM python:3.11-slim AS base

LABEL maintainer="DevOps Team"
LABEL description="Enterprise DevOps MCP Server - AI DevOps 工具服务层"

WORKDIR /app

# 安装系统依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-client \
        curl \
        && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: 生产镜像 ----
FROM base AS production

WORKDIR /app

# 复制应用代码
COPY app/ ./app/
COPY .env.example .env.example
COPY mcp_config_examples/ ./mcp_config_examples/

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 暴露 MCP 服务端口（SSE 模式）
EXPOSE 8000

# 启动命令（stdio 传输模式）
ENTRYPOINT ["python", "-m", "app.server"]

# ---- Stage 3: 测试镜像 ----
FROM base AS testing

WORKDIR /app

COPY app/ ./app/
COPY tests/ ./tests/
COPY .env.example .env.example
COPY pytest.ini .
COPY requirements.txt .

# 安装测试依赖
RUN pip install --no-cache-dir pytest pytest-asyncio

# 运行测试（使用模拟环境，无需真实基础设施）
CMD ["python", "-m", "pytest", "tests/", "-v"]