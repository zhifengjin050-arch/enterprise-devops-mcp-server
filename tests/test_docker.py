"""Docker 工具模块测试。

测试 docker.py 中三个 MCP Tool 的功能：
- docker_list：容器列表
- docker_logs：容器日志
- docker_restart：容器重启（权限控制）

使用 mock 避免强依赖真实 Docker 环境。
"""

from unittest.mock import MagicMock, patch

import pytest
from docker.errors import APIError, DockerException, NotFound

from fastmcp import FastMCP


# ---- Fixtures ----

@pytest.fixture
def mcp_server() -> FastMCP:
    """创建测试用 FastMCP 实例。"""
    return FastMCP(name="Test MCP Server")


@pytest.fixture
def mock_client() -> MagicMock:
    """创建模拟 DockerClient。"""
    client = MagicMock()

    # 模拟容器对象
    container1 = MagicMock()
    container1.name = "nginx"
    container1.short_id = "abc123"
    container1.status = "running"
    container1.ports = {"80/tcp": [{"HostPort": "80"}]}
    container1.image.tags = ["nginx:latest"]
    container1.image.short_id = "sha256:xxx"

    container2 = MagicMock()
    container2.name = "redis"
    container2.short_id = "def456"
    container2.status = "running"
    container2.ports = {"6379/tcp": [{"HostPort": "6379"}]}
    container2.image.tags = ["redis:7"]
    container2.image.short_id = "sha256:yyy"

    stopped = MagicMock()
    stopped.name = "old-app"
    stopped.short_id = "ghi789"
    stopped.status = "exited"
    stopped.ports = {}
    stopped.image.tags = ["myapp:v1"]
    stopped.image.short_id = "sha256:zzz"

    client.containers.list.return_value = [container1, container2, stopped]
    client.containers.get.return_value = container1

    return client


# ---- Helper 函数测试 ----

class TestDockerHelpers:
    """docker.py 辅助函数测试。"""

    def test_parse_ports_with_mappings(self) -> None:
        """验证 _parse_ports 正确解析端口映射。"""
        from app.tools.docker import _parse_ports

        mock_container = MagicMock()
        mock_container.ports = {"80/tcp": [{"HostPort": "80"}], "443/tcp": [{"HostPort": "443"}]}
        result = _parse_ports(mock_container)
        assert "80:80/tcp" in result
        assert "443:443/tcp" in result

    def test_parse_ports_without_mappings(self) -> None:
        """验证 _parse_ports 在没有端口映射时返回 '-'。"""
        from app.tools.docker import _parse_ports

        mock_container = MagicMock()
        mock_container.ports = {}
        result = _parse_ports(mock_container)
        assert result == "-"

    def test_parse_ports_with_exposed_only(self) -> None:
        """验证 _parse_ports 处理只暴露未映射的端口。"""
        from app.tools.docker import _parse_ports

        mock_container = MagicMock()
        mock_container.ports = {"80/tcp": None}
        result = _parse_ports(mock_container)
        assert "-:80/tcp" in result


# ---- docker_list 测试 ----

class TestDockerList:
    """docker_list Tool 测试用例。"""

    @patch("app.tools.docker.docker.from_env")
    def test_returns_list_of_dicts(self, mock_from_env: MagicMock, mock_client: MagicMock) -> None:
        """验证 docker_list 返回 list[dict] 格式。"""
        mock_from_env.return_value = mock_client
        from app.tools.docker import docker_list

        result = docker_list()
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, dict) for item in result)

    @patch("app.tools.docker.docker.from_env")
    def test_contains_expected_keys(self, mock_from_env: MagicMock, mock_client: MagicMock) -> None:
        """验证每个容器包含 name, image, status, ports 字段。"""
        mock_from_env.return_value = mock_client
        from app.tools.docker import docker_list

        result = docker_list()
        for item in result:
            assert "name" in item
            assert "image" in item
            assert "status" in item
            assert "ports" in item

    @patch("app.tools.docker.docker.from_env")
    def test_all_containers_param(self, mock_from_env: MagicMock, mock_client: MagicMock) -> None:
        """验证 all_containers=True 时传参正确。"""
        mock_from_env.return_value = mock_client
        from app.tools.docker import docker_list

        docker_list(all_containers=True)
        mock_client.containers.list.assert_called_with(all=True)

    @patch("app.tools.docker.docker.from_env")
    def test_handles_docker_exception(self, mock_from_env: MagicMock) -> None:
        """验证 Docker 连接异常时返回错误列表。"""
        mock_from_env.side_effect = DockerException("Docker 服务未运行")
        from app.tools.docker import docker_list

        result = docker_list()
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["status"] == "error"

    @patch("app.tools.docker.docker.from_env")
    def test_handles_api_error(self, mock_from_env: MagicMock) -> None:
        """验证 Docker API 错误时返回错误列表。"""
        mock_from_env.side_effect = APIError("API 错误")
        from app.tools.docker import docker_list

        result = docker_list()
        assert isinstance(result, list)
        assert result[0]["status"] == "error"


# ---- docker_logs 测试 ----

class TestDockerLogs:
    """docker_logs Tool 测试用例。"""

    @patch("app.tools.docker.docker.from_env")
    def test_returns_expected_structure(self, mock_from_env: MagicMock, mock_client: MagicMock) -> None:
        """验证 docker_logs 返回含 container 和 logs 的字典。"""
        mock_container = MagicMock()
        mock_container.logs.return_value = b"2024-01-01 access log line 1\n2024-01-01 access log line 2\n"
        mock_client.containers.get.return_value = mock_container
        mock_from_env.return_value = mock_client

        from app.tools.docker import docker_logs
        result = docker_logs(container_name="nginx")

        assert "container" in result
        assert "logs" in result
        assert result["container"] == "nginx"

    @patch("app.tools.docker.docker.from_env")
    def test_logs_content(self, mock_from_env: MagicMock, mock_client: MagicMock) -> None:
        """验证 docker_logs 返回正确的日志内容。"""
        mock_container = MagicMock()
        mock_container.logs.return_value = b"line1\nline2\nline3\n"
        mock_client.containers.get.return_value = mock_container
        mock_from_env.return_value = mock_client

        from app.tools.docker import docker_logs
        result = docker_logs(container_name="nginx", lines=3)
        assert "line1" in result["logs"]
        assert "line3" in result["logs"]

    @patch("app.tools.docker.docker.from_env")
    def test_handles_not_found(self, mock_from_env: MagicMock, mock_client: MagicMock) -> None:
        """验证容器不存在时返回 error。"""
        mock_client.containers.get.side_effect = NotFound("容器未找到")
        mock_from_env.return_value = mock_client

        from app.tools.docker import docker_logs
        result = docker_logs(container_name="nonexistent")
        assert result["status"] == "error"
        assert "不存在" in result["message"]

    @patch("app.tools.docker.docker.from_env")
    def test_handles_docker_exception(self, mock_from_env: MagicMock) -> None:
        """验证 Docker 连接异常时返回 error。"""
        mock_from_env.side_effect = DockerException("Docker 未运行")
        from app.tools.docker import docker_logs

        result = docker_logs(container_name="nginx")
        assert result["status"] == "error"


# ---- docker_restart 测试 ----

class TestDockerRestart:
    """docker_restart Tool 测试用例（含权限检查）。"""

    @patch("app.tools.docker.docker.from_env")
    def test_restart_success(self, mock_from_env: MagicMock, mock_client: MagicMock) -> None:
        """验证 docker_restart 成功时返回正确结构。"""
        mock_container = MagicMock()
        mock_client.containers.get.return_value = mock_container
        mock_from_env.return_value = mock_client

        from app.tools.docker import docker_restart
        # 注意：默认 execute_tools_enabled=False，需要在测试前设置
        from app.config import settings
        original_value = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = True
            result = docker_restart(container_name="nginx")
        finally:
            settings.execute_tools_enabled = original_value

        assert result["container"] == "nginx"
        assert result["action"] == "restart"
        assert result["status"] == "success"
        mock_container.restart.assert_called_once_with(timeout=10)

    @patch("app.tools.docker.docker.from_env")
    def test_restart_denied_without_execute_permission(
        self, mock_from_env: MagicMock, mock_client: MagicMock
    ) -> None:
        """验证 execute_tools_enabled=False 时拒绝执行。"""
        mock_from_env.return_value = mock_client

        from app.tools.docker import docker_restart
        # 确保 execute_tools_enabled 为 False（默认值）
        from app.config import settings
        original_value = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = False
            result = docker_restart(container_name="nginx")
        finally:
            settings.execute_tools_enabled = original_value

        assert result["error"] == "execute_permission_denied"
        # 确认容器没有被重启
        mock_client.containers.get.assert_not_called()

    @patch("app.tools.docker.docker.from_env")
    def test_restart_not_found(self, mock_from_env: MagicMock, mock_client: MagicMock) -> None:
        """验证重启不存在的容器时返回 error。"""
        mock_client.containers.get.side_effect = NotFound("未找到")
        mock_from_env.return_value = mock_client

        from app.tools.docker import docker_restart
        from app.config import settings
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = True
            result = docker_restart(container_name="nonexistent")
        finally:
            settings.execute_tools_enabled = original

        assert result["status"] == "error"
        assert "不存在" in result["message"]

    @patch("app.tools.docker.docker.from_env")
    def test_restart_api_error(self, mock_from_env: MagicMock, mock_client: MagicMock) -> None:
        """验证 Docker API 错误时返回 error。"""
        mock_container = MagicMock()
        mock_container.restart.side_effect = APIError("API 调用失败")
        mock_client.containers.get.return_value = mock_container
        mock_from_env.return_value = mock_client

        from app.tools.docker import docker_restart
        from app.config import settings
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = True
            result = docker_restart(container_name="nginx")
        finally:
            settings.execute_tools_enabled = original

        assert result["status"] == "error"


# ---- MCP 注册测试 ----

class TestDockerRegistration:
    """Docker Tool MCP 注册测试。"""

    def test_three_tools_registered(self, mcp_server: FastMCP) -> None:
        """验证 Docker 模块注册了 3 个 Tool（docker_list, docker_logs, docker_restart）。"""
        from app.tools.docker import register_docker_tools

        register_docker_tools(mcp_server)

        tool_manager = getattr(mcp_server._mcp_server, "_tool_manager", None)
        if tool_manager:
            tools = getattr(tool_manager, "_tools", {})
            assert len(tools) == 3, f"Docker 模块应注册 3 个 Tool，实际: {len(tools)}"

    def test_all_tool_names(self, mcp_server: FastMCP) -> None:
        """验证 3 个 Tool 的名称正确。"""
        from app.tools.docker import register_docker_tools

        register_docker_tools(mcp_server)

        tool_manager = getattr(mcp_server._mcp_server, "_tool_manager", None)
        if tool_manager:
            tools = getattr(tool_manager, "_tools", {})
            tool_names = [t.name for t in tools.values()]
            assert "docker_list" in tool_names, "docker_list 应已注册"
            assert "docker_logs" in tool_names, "docker_logs 应已注册"
            assert "docker_restart" in tool_names, "docker_restart 应已注册"