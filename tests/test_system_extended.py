"""System 扩展工具测试（V1.0.1）。

测试新实现的系统工具：
- get_system_info
- get_cpu_usage
- get_memory_usage
- get_disk_usage
- list_processes
- get_audit_logs
"""

from unittest.mock import patch, MagicMock

import pytest

from app.tools.system import (
    get_system_info,
    get_cpu_usage,
    get_memory_usage,
    get_disk_usage,
    list_processes,
    get_audit_logs,
)


class TestGetSystemInfo:
    """get_system_info 测试。"""

    def test_returns_dict(self) -> None:
        """验证返回字典。"""
        result = get_system_info()
        assert isinstance(result, dict)

    def test_contains_expected_keys(self) -> None:
        """验证返回结构包含所有期望字段。"""
        result = get_system_info()
        expected_keys = {"hostname", "os", "platform", "python_version", "uptime"}
        assert expected_keys.issubset(result.keys())

    def test_hostname_is_string(self) -> None:
        """验证 hostname 返回字符串。"""
        result = get_system_info()
        assert isinstance(result["hostname"], str)
        assert len(result["hostname"]) > 0

    def test_os_is_string(self) -> None:
        """验证操作系统信息。"""
        result = get_system_info()
        assert isinstance(result["os"], str)

    def test_python_version_valid(self) -> None:
        """验证 Python 版本格式。"""
        result = get_system_info()
        parts = result["python_version"].split(".")
        assert len(parts) >= 2
        assert all(p.isdigit() or p[0].isdigit() for p in parts)

    def test_uptime_is_string(self) -> None:
        """验证 uptime 返回字符串。"""
        result = get_system_info()
        assert isinstance(result["uptime"], str)

    def test_error_handling(self) -> None:
        """验证异常处理。"""
        with patch("app.tools.system._collect_system_info", side_effect=RuntimeError("test error")):
            result = get_system_info()
            assert result["status"] == "error"


class TestGetCpuUsage:
    """get_cpu_usage 测试。"""

    def test_returns_dict(self) -> None:
        """验证返回字典。"""
        result = get_cpu_usage()
        assert isinstance(result, dict)

    def test_contains_expected_keys(self) -> None:
        """验证返回结构包含所有期望字段。"""
        result = get_cpu_usage()
        expected_keys = {"cpu_percent", "cpu_count"}
        assert expected_keys.issubset(result.keys())

    def test_cpu_percent_in_range(self) -> None:
        """验证 CPU 百分比在合理范围内。"""
        result = get_cpu_usage()
        assert 0.0 <= result["cpu_percent"] <= 100.0

    def test_cpu_count_positive(self) -> None:
        """验证 CPU 核心数大于 0。"""
        result = get_cpu_usage()
        assert result["cpu_count"] > 0

    def test_error_handling(self) -> None:
        """验证异常处理。"""
        with patch("app.tools.system._collect_cpu_usage", side_effect=RuntimeError("test error")):
            result = get_cpu_usage()
            assert result["status"] == "error"


class TestGetMemoryUsage:
    """get_memory_usage 测试。"""

    def test_returns_dict(self) -> None:
        """验证返回字典。"""
        result = get_memory_usage()
        assert isinstance(result, dict)

    def test_contains_expected_keys(self) -> None:
        """验证返回结构包含所有期望字段。"""
        result = get_memory_usage()
        expected_keys = {"total", "used", "available", "percent"}
        assert expected_keys.issubset(result.keys())

    def test_total_positive(self) -> None:
        """验证总内存大于 0。"""
        result = get_memory_usage()
        assert result["total"] > 0

    def test_percent_in_range(self) -> None:
        """验证内存百分比在合理范围内。"""
        result = get_memory_usage()
        assert 0.0 <= result["percent"] <= 100.0

    def test_used_plus_available_less_than_total(self) -> None:
        """验证已用+可用不超过总量。"""
        result = get_memory_usage()
        assert result["used"] + result["available"] <= result["total"] * 1.1

    def test_error_handling(self) -> None:
        """验证异常处理。"""
        with patch("app.tools.system._collect_memory_usage", side_effect=RuntimeError("test error")):
            result = get_memory_usage()
            assert result["status"] == "error"


class TestGetDiskUsage:
    """get_disk_usage 测试。"""

    def test_returns_list(self) -> None:
        """验证返回列表。"""
        result = get_disk_usage()
        assert isinstance(result, list)

    def test_first_item_has_expected_keys(self) -> None:
        """验证返回结构包含所有期望字段。"""
        result = get_disk_usage()
        if result:
            expected_keys = {"path", "total", "used", "free", "percent"}
            assert expected_keys.issubset(result[0].keys())

    def test_root_partition_exists(self) -> None:
        """验证系统根分区存在（跨平台兼容）。"""
        import sys
        result = get_disk_usage()
        paths = [item.get("path") for item in result]
        if sys.platform == "win32":
            # Windows 根分区通常为 C:\
            assert any(p.endswith(":\\") for p in paths)
        else:
            assert "/" in paths

    def test_percent_in_range(self) -> None:
        """验证磁盘百分比在合理范围内。"""
        result = get_disk_usage()
        for item in result:
            if "percent" in item:
                assert 0.0 <= item["percent"] <= 100.0

    def test_error_handling(self) -> None:
        """验证异常处理。"""
        with patch("app.tools.system._collect_disk_usage", side_effect=RuntimeError("test error")):
            result = get_disk_usage()
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["status"] == "error"


class TestListProcesses:
    """list_processes 测试。"""

    def test_returns_list(self) -> None:
        """验证返回列表。"""
        result = list_processes(limit=5)
        assert isinstance(result, list)

    def test_default_limit(self) -> None:
        """验证默认返回 10 个进程。"""
        result = list_processes()
        assert len(result) <= 10

    def test_custom_limit(self) -> None:
        """验证自定义 limit 生效。"""
        result = list_processes(limit=3)
        assert len(result) <= 3

    def test_first_item_has_expected_keys(self) -> None:
        """验证返回结构包含所有期望字段。"""
        result = list_processes(limit=1)
        if result:
            expected_keys = {"pid", "name", "cpu_percent", "memory_percent"}
            assert expected_keys.issubset(result[0].keys())

    def test_sorted_by_cpu(self) -> None:
        """验证按 CPU 使用率降序排列。"""
        result = list_processes(limit=15)
        if len(result) >= 2:
            assert result[0]["cpu_percent"] >= result[-1]["cpu_percent"]

    def test_error_handling(self) -> None:
        """验证异常处理。"""
        with patch("app.tools.system._collect_processes", side_effect=RuntimeError("test error")):
            result = list_processes()
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["status"] == "error"


class TestGetAuditLogs:
    """get_audit_logs 测试。"""

    def test_returns_dict(self) -> None:
        """验证返回字典。"""
        result = get_audit_logs(count=1)
        assert isinstance(result, dict)

    def test_contains_logs_and_stats(self) -> None:
        """验证返回结构包含 logs 和 stats。"""
        result = get_audit_logs(count=1)
        assert "logs" in result
        assert "stats" in result

    def test_logs_is_list(self) -> None:
        """验证 logs 是列表。"""
        result = get_audit_logs(count=1)
        assert isinstance(result["logs"], list)

    def test_stats_contains_expected_keys(self) -> None:
        """验证 stats 包含统计字段。"""
        result = get_audit_logs(count=1)
        stats = result["stats"]
        expected_keys = {"total_calls", "success", "error", "permission_denied", "avg_duration_ms", "tools_used"}
        assert expected_keys.issubset(stats.keys())

    def test_count_limit(self) -> None:
        """验证 count 参数限制。"""
        result = get_audit_logs(count=200)
        assert len(result["logs"]) <= 100

    def test_count_minimum(self) -> None:
        """验证 count 最小值为 1。"""
        result = get_audit_logs(count=0)
        assert len(result["logs"]) >= 0

    def test_error_handling(self) -> None:
        """验证异常处理。"""
        with patch("app.tools.system.get_audit_logger", side_effect=RuntimeError("test error")):
            result = get_audit_logs()
            assert result["status"] == "error"


class TestConfirmExecuteAction:
    def test_rejects_unknown_tool(self) -> None:
        from app.tools.system import confirm_execute_action

        result = confirm_execute_action(tool_name="not_a_tool")
        assert result["status"] == "error"

    def test_confirms_known_tool(self) -> None:
        from app.security.execute_protection import ProtectionLevel, get_execute_protector
        from app.tools.system import confirm_execute_action

        protector = get_execute_protector()
        protector.level = ProtectionLevel.STRICT
        protector.reset_confirmation()
        result = confirm_execute_action(tool_name="docker_restart")
        assert result["status"] == "success"
        assert protector.require_confirmation("docker_restart") is True
        protector.reset_confirmation()
        protector.level = ProtectionLevel.BASIC


class TestRegistration:
    """注册完整性测试。"""

    def test_all_tools_registered(self) -> None:
        """验证所有 7 个 system Tool 注册。"""
        import asyncio
        from fastmcp import FastMCP
        from app.tools.system import register_system_tools

        mcp = FastMCP("test")
        register_system_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        names = [t.name for t in tools]
        assert "get_server_health" in names
        assert "get_system_info" in names
        assert "get_cpu_usage" in names
        assert "get_memory_usage" in names
        assert "get_disk_usage" in names
        assert "get_audit_logs" in names
        assert "list_processes" in names
        assert "confirm_execute_action" in names
        assert len(tools) == 8