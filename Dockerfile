# ------------------------------------------------------------
# Enterprise DevOps MCP Server - Docker 镜像
# ------------------------------------------------------------
# targets:
#   production  — 运行 MCP Server（默认 stdio；也可挂到编排侧）
#   testing     — 容器内执行 pytest
# ------------------------------------------------------------

# ---- Stage 1: 基础依赖 ----
FROM python:3.11-slim AS base

LABEL maintainer="DevOps Team"
LABEL description="Enterprise DevOps MCP Server - AI DevOps MCP Tool Server"

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-client \
        curl \
        && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: 生产镜像 ----
FROM base AS production

WORKDIR /app

COPY app/ ./app/
COPY .env.example .env.example
COPY mcp_config_examples/ ./mcp_config_examples/
COPY scripts/ ./scripts/

# stdio MCP 无 HTTP 端口；用模块导入探活
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from app.config import settings; assert settings.mcp_server_name" || exit 1

ENV ENABLE_SECURITY=true \
    EXECUTE_TOOLS_ENABLED=false \
    AUDIT_LOG_ENABLED=true \
    LOG_LEVEL=INFO

ENTRYPOINT ["python", "-m", "app.server"]

# ---- Stage 3: 测试镜像 ----
FROM base AS testing

WORKDIR /app

COPY app/ ./app/
COPY tests/ ./tests/
COPY .env.example .env.example
COPY pytest.ini .
COPY requirements.txt .

RUN pip install --no-cache-dir pytest pytest-asyncio

ENV ENABLE_SECURITY=true \
    EXECUTE_TOOLS_ENABLED=false \
    AUDIT_LOG_ENABLED=true \
    LOG_LEVEL=WARNING

CMD ["python", "-m", "pytest", "tests/", "-v"]
