"""MCP 集成测试。

验证 MCP Server 的完整功能：
1. Server 正确初始化
2. Tool 正确注册
3. Tool 名称和描述符合 MCP 规范
4. 权限校验与注册一致
"""

import asyncio
from unittest.mock import patch, MagicMock

import pytest

from fastmcp import FastMCP


@pytest.fixture
def server() -> FastMCP:
    """创建全新的 FastMCP 实例并注册所有 Tool（避免全局实例重复注册）。"""
    mcp = FastMCP(
        name="Enterprise DevOps MCP Server",
        version="1.0.1",
    )
    from app.tools import register_all_tools
    register_all_tools(mcp)
    return mcp


class TestServerInitialization:
    """MCP Server 初始化测试。"""

    def test_server_initializes(self, server: FastMCP) -> None:
        """验证 Server 初始化成功。"""
        assert server is not None
        assert server.name == "Enterprise DevOps MCP Server"
        assert server.version == "1.0.1"

    def test_server_has_run_method(self, server: FastMCP) -> None:
        """验证 Server 支持 run 方法（stdio transport 就绪）。"""
        assert hasattr(server, "run")
        assert hasattr(server, "run_async")


class TestToolRegistration:
    """Tool 注册完整性测试。"""

    def test_all_modules_registered(self) -> None:
        """验证 4 个模块全部注册成功。"""
        from app.tools import get_registered_modules
        modules = get_registered_modules()
        assert "system" in modules
        assert "docker" in modules
        assert "kubernetes" in modules
        assert "ssh" in modules

    @pytest.mark.asyncio
    async def test_discover_all_tools(self, server: FastMCP) -> None:
        """验证 MCP Client 可以发现所有 Tool。"""
        tools = await server.list_tools()
        tool_names = [t.name for t in tools]

        # 必须包含的 Tool
        assert "get_server_health" in tool_names
        assert "docker_list" in tool_names
        assert "docker_logs" in tool_names
        assert "docker_restart" in tool_names

        # 骨架 Tool 也应存在
        assert "get_system_info" in tool_names
        assert "get_cpu_usage" in tool_names
        assert "get_memory_usage" in tool_names
        assert "get_disk_usage" in tool_names
        assert "list_processes" in tool_names

        # SSH Tool
        assert "ssh_check_connection" in tool_names
        assert "ssh_execute_command" in tool_names
        assert "ssh_upload_file" in tool_names

        # Kubernetes Tool
        assert "k8s_get_pods" in tool_names
        assert "k8s_get_deployments" in tool_names
        assert "k8s_get_services" in tool_names
        assert "k8s_logs" in tool_names

    @pytest.mark.asyncio
    async def test_tool_count(self, server: FastMCP) -> None:
        """验证 Tool 总数正确（7 system + 3 docker + 4 k8s + 3 ssh_realtime = 17）。"""
        tools = await server.list_tools()
        assert len(tools) == 17, (
            f"期望 17 个 Tool，实际: {len(tools)}"
        )

    @pytest.mark.asyncio
    async def test_tool_names_unique(self, server: FastMCP) -> None:
        """验证所有 Tool 名称唯一。"""
        tools = await server.list_tools()
        names = [t.name for t in tools]
        assert len(names) == len(set(names)), (
            f"Tool 名称存在重复: {names}"
        )


class TestToolMetadata:
    """Tool Metadata（name / description / schema）验证。"""

    @pytest.mark.asyncio
    async def test_get_server_health_metadata(self, server: FastMCP) -> None:
        """验证 get_server_health 的 Metadata 完整性。"""
        tools = await server.list_tools()
        health_tool = next(t for t in tools if t.name == "get_server_health")

        assert health_tool.name == "get_server_health"
        assert health_tool.description is not None
        assert len(health_tool.description) > 0
        # 检查 description 是否包含关键信息
        desc = health_tool.description
        assert "CPU" in desc
        assert "healthy" in desc.lower()
        assert "warning" in desc.lower()
        assert "critical" in desc.lower()

    @pytest.mark.asyncio
    async def test_docker_list_metadata(self, server: FastMCP) -> None:
        """验证 docker_list 的 Metadata 完整性。"""
        tools = await server.list_tools()
        dl_tool = next(t for t in tools if t.name == "docker_list")

        assert dl_tool.name == "docker_list"
        assert dl_tool.description is not None
        assert len(dl_tool.description) > 0

        # 检查参数 schema（FastMCP 3.x 使用 parameters）
        assert dl_tool.parameters is not None
        properties = dl_tool.parameters.get("properties", {})
        assert "all_containers" in properties

    @pytest.mark.asyncio
    async def test_docker_logs_metadata(self, server: FastMCP) -> None:
        """验证 docker_logs 的 Metadata 完整性。"""
        tools = await server.list_tools()
        logs_tool = next(t for t in tools if t.name == "docker_logs")

        assert logs_tool.name == "docker_logs"
        assert logs_tool.description is not None

        assert logs_tool.parameters is not None
        properties = logs_tool.parameters.get("properties", {})
        assert "container_name" in properties
        assert "lines" in properties

    @pytest.mark.asyncio
    async def test_docker_restart_metadata(self, server: FastMCP) -> None:
        """验证 docker_restart 的 Metadata 完整性。"""
        tools = await server.list_tools()
        restart_tool = next(t for t in tools if t.name == "docker_restart")

        assert restart_tool.name == "docker_restart"
        assert restart_tool.description is not None

        assert restart_tool.parameters is not None
        properties = restart_tool.parameters.get("properties", {})
        assert "container_name" in properties


class TestToolExecution:
    """Tool 执行集成测试（使用 mock 避免真实环境依赖）。"""

    @pytest.mark.asyncio
    async def test_get_server_health_returns_valid_data(self, server: FastMCP) -> None:
        """验证 get_server_health 返回有效健康数据。"""
        result = await server.call_tool("get_server_health", {})
        # FastMCP 返回 ToolResult 对象
        assert result is not None

        # 提取 content 并验证
        for content in result.content:
            if hasattr(content, "text") and content.text:
                import json
                data = json.loads(content.text)
                assert "hostname" in data
                assert "status" in data

    @pytest.mark.asyncio
    async def test_docker_list_handles_no_docker(self, server: FastMCP) -> None:
        """验证 Docker 未安装时 docker_list 返回错误而非崩溃。"""
        import docker
        from docker.errors import DockerException

        # mock docker.from_env 触发异常
        original_from_env = docker.from_env
        docker.from_env = MagicMock(side_effect=DockerException("模拟: Docker 未运行"))

        try:
            result = await server.call_tool("docker_list", {})
            assert result is not None
        finally:
            docker.from_env = original_from_env


class TestPermissionIntegration:
    """权限与注册一致性测试。"""

    def test_security_enabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """验证代码默认值：安全模式默认启用（不受本地 .env 干扰）。"""
        monkeypatch.delenv("ENABLE_SECURITY", raising=False)
        from app.config import Settings

        defaults = Settings(_env_file=None)
        assert defaults.enable_security is True

    def test_execute_disabled_by_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """验证代码默认值：执行操作默认关闭（不受本地 .env 干扰）。"""
        monkeypatch.delenv("EXECUTE_TOOLS_ENABLED", raising=False)
        from app.config import Settings

        defaults = Settings(_env_file=None)
        assert defaults.execute_tools_enabled is False

    @pytest.mark.asyncio
    async def test_tool_permission_returns_error_struct(self, server: FastMCP) -> None:
        """验证调用不存在的 Tool 时抛出 NotFoundError 而不崩溃。"""
        from fastmcp.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await server.call_tool("nonexistent_tool", {})


class TestStdioTransport:
    """stdio transport 支持测试。"""

    def test_server_supports_stdio(self, server: FastMCP) -> None:
        """验证 Server 支持 stdio transport（通过 run_async 方法）。"""
        assert hasattr(server, "run_stdio_async"), (
            "Server 应支持 run_stdio_async 方法（MCP stdio transport）"
        )