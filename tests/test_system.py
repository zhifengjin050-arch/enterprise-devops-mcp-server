"""System 工具模块测试。

测试 system.py 中注册的 Tool 函数，包括：
- get_server_health 真实逻辑（模块级函数，独立可测）
- 骨架 Tool 注册
"""

import pytest

from fastmcp import FastMCP


@pytest.fixture
def mcp_server() -> FastMCP:
    """创建测试用 FastMCP 实例。"""
    return FastMCP(name="Test MCP Server")


class TestSystemTools:
    """System Tool 注册测试用例。"""

    def test_tool_registration_count(self, mcp_server: FastMCP) -> None:
        """验证 System 模块注册了预期数量的 Tool（6 个）。"""
        from app.tools.system import register_system_tools

        register_system_tools(mcp_server)

        tool_manager = getattr(mcp_server._mcp_server, "_tool_manager", None)
        if tool_manager:
            tools = getattr(tool_manager, "_tools", {})
            assert len(tools) == 8, (
                f"System 模块应注册 8 个 Tool，实际: {len(tools)}"
            )

    def test_health_tool_registered(self, mcp_server: FastMCP) -> None:
        """验证 get_server_health 已注册为 MCP Tool。"""
        from app.tools.system import register_system_tools

        register_system_tools(mcp_server)

        tool_manager = getattr(mcp_server._mcp_server, "_tool_manager", None)
        if tool_manager:
            tools = getattr(tool_manager, "_tools", {})
            tool_names = [t.name for t in tools.values()]
            assert "get_server_health" in tool_names, (
                "get_server_health 应已注册"
            )


class TestServerHealth:
    """get_server_health 模块级函数测试用例。"""

    def test_returns_dict(self) -> None:
        """验证 get_server_health 返回 dict 类型。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        assert isinstance(result, dict)

    def test_has_hostname_field(self) -> None:
        """验证结果包含 hostname 字段。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        assert "hostname" in result
        assert isinstance(result["hostname"], str)
        assert len(result["hostname"]) > 0

    def test_has_cpu_usage_field(self) -> None:
        """验证结果包含 cpu_usage 字段且为数值。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        assert "cpu_usage" in result
        assert isinstance(result["cpu_usage"], (int, float))

    def test_cpu_usage_in_range(self) -> None:
        """验证 CPU 使用率在 0-100 合理范围。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        cpu = result["cpu_usage"]
        assert 0.0 <= cpu <= 100.0, (
            f"CPU 使用率应在 0~100 之间，实际: {cpu}"
        )

    def test_has_memory_usage_field(self) -> None:
        """验证结果包含 memory_usage 字段且为数值。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        assert "memory_usage" in result
        assert isinstance(result["memory_usage"], (int, float))

    def test_memory_usage_in_range(self) -> None:
        """验证内存使用率在 0-100 合理范围。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        mem = result["memory_usage"]
        assert 0.0 <= mem <= 100.0, (
            f"内存使用率应在 0~100 之间，实际: {mem}"
        )

    def test_has_disk_usage_field(self) -> None:
        """验证结果包含 disk_usage 字段且为数值。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        assert "disk_usage" in result
        assert isinstance(result["disk_usage"], (int, float))

    def test_disk_usage_in_range(self) -> None:
        """验证磁盘使用率在 0-100 合理范围。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        disk = result["disk_usage"]
        assert 0.0 <= disk <= 100.0, (
            f"磁盘使用率应在 0~100 之间，实际: {disk}"
        )

    def test_has_uptime_field(self) -> None:
        """验证结果包含 uptime 字段。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        assert "uptime" in result
        assert isinstance(result["uptime"], str)

    def test_has_status_field(self) -> None:
        """验证结果包含 status 字段且为合法值。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        assert "status" in result
        assert result["status"] in ("healthy", "warning", "critical", "error"), (
            f"status 应为 healthy/warning/critical/error 之一，实际: {result['status']}"
        )

    def test_json_structure_complete(self) -> None:
        """验证返回的 JSON 字段完整。"""
        from app.tools.system import get_server_health

        result = get_server_health()
        expected_fields = {
            "hostname", "cpu_usage", "memory_usage",
            "disk_usage", "uptime", "status",
        }
        assert set(result.keys()) == expected_fields, (
            f"返回字段不匹配。期望: {expected_fields}, 实际: {set(result.keys())}"
        )

    def test_healthy_determination(self) -> None:
        """验证健康状态判定逻辑：全部指标 < 80% 为 healthy。"""
        from app.tools.system import _determine_health_status

        assert _determine_health_status(30.0, 50.0, 40.0) == "healthy"

    def test_warning_determination(self) -> None:
        """验证健康状态判定逻辑：任一指标 >= 80% 为 warning。"""
        from app.tools.system import _determine_health_status

        assert _determine_health_status(85.0, 50.0, 40.0) == "warning"
        assert _determine_health_status(30.0, 90.0, 40.0) == "warning"

    def test_critical_determination(self) -> None:
        """验证健康状态判定逻辑：任一指标 >= 95% 为 critical。"""
        from app.tools.system import _determine_health_status

        assert _determine_health_status(96.0, 50.0, 40.0) == "critical"
        assert _determine_health_status(30.0, 50.0, 98.0) == "critical"


class TestServerHealthErrorHandling:
    """get_server_health 异常处理测试。"""

    def test_handles_psutil_error(self) -> None:
        """验证 psutil 异常时通过 get_server_health 返回 error 状态。"""
        import psutil
        from app.tools.system import get_server_health

        original_cpu = psutil.cpu_percent
        original_mem = psutil.virtual_memory
        original_disk = psutil.disk_usage
        original_boot = psutil.boot_time

        def _mock_error(*args: object, **kwargs: object) -> None:
            raise psutil.Error("模拟系统资源获取失败")

        try:
            psutil.cpu_percent = _mock_error  # type: ignore[assignment]

            result = get_server_health()

            assert "status" in result
            assert result["status"] == "error"
            assert "message" in result
        finally:
            psutil.cpu_percent = original_cpu
            psutil.virtual_memory = original_mem
            psutil.disk_usage = original_disk
            psutil.boot_time = original_boot


class TestUptimeFormatting:
    """_format_uptime 工具函数测试。"""

    def test_returns_string(self) -> None:
        """验证 _format_uptime 返回字符串。"""
        from app.tools.system import _format_uptime

        import time
        # 使用 2 小时前作为启动时间，确保 "hour" 一定出现
        result = _format_uptime(time.time() - 7200)
        assert isinstance(result, str)
        assert "hour" in result or "hours" in result

    def test_recent_boot(self) -> None:
        """验证刚启动时显示分钟。"""
        from app.tools.system import _format_uptime

        import time
        result = _format_uptime(time.time() - 300)
        assert isinstance(result, str)
        assert "minute" in result