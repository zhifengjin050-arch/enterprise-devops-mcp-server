"""增强权限模块测试（Day 5 新增功能）。"""

import pytest

from app.security.permission import (
    PermissionManager,
    OperationType,
    PermissionResult,
)
from app.config import settings


class TestOperationType:
    """OperationType 枚举测试。"""

    def test_enum_values(self) -> None:
        """验证枚举值。"""
        assert OperationType.READ.value == "read"
        assert OperationType.EXECUTE.value == "execute"


class TestClassifyOperation:
    """classify_operation 方法测试。"""

    def test_read_only_tool(self) -> None:
        """验证只读工具分类为 READ。"""
        pm = PermissionManager()
        assert pm.classify_operation("get_server_health") == OperationType.READ
        assert pm.classify_operation("docker_list") == OperationType.READ
        assert pm.classify_operation("docker_logs") == OperationType.READ

    def test_execute_tool(self) -> None:
        """验证执行工具分类为 EXECUTE。"""
        pm = PermissionManager()
        assert pm.classify_operation("docker_restart") == OperationType.EXECUTE


class TestPermissionResult:
    """PermissionResult 数据类测试。"""

    def test_allowed_result(self) -> None:
        """验证允许通过的结果。"""
        result = PermissionResult(
            allowed=True,
            operation_type=OperationType.READ,
            tool_name="get_server_health",
            module_name="system",
        )
        assert result.allowed is True
        assert result.reason == ""

    def test_denied_result(self) -> None:
        """验证拒绝的结果。"""
        result = PermissionResult(
            allowed=False,
            operation_type=OperationType.READ,
            reason="Tool 'xxx' 不在白名单中",
            tool_name="xxx",
            module_name="xxx",
        )
        assert result.allowed is False
        assert "不在白名单中" in result.reason

    def test_security_context(self) -> None:
        """验证安全上下文。"""
        result = PermissionResult(
            allowed=True,
            tool_name="tool",
            module_name="module",
            security_context={"caller": "test", "request_id": "req123"},
        )
        assert result.security_context["caller"] == "test"
        assert result.security_context["request_id"] == "req123"


class TestCheckPermissionDetailed:
    """check_permission_detailed 方法测试。"""

    def test_allows_system_module(self) -> None:
        """验证 system 模块通过详细检查。"""
        pm = PermissionManager()
        result = pm.check_permission_detailed("system")
        assert result.allowed is True
        assert result.operation_type == OperationType.READ
        assert result.module_name == "system"

    def test_allows_docker_module(self) -> None:
        """验证 docker 模块通过详细检查。"""
        pm = PermissionManager()
        result = pm.check_permission_detailed("docker")
        assert result.allowed is True
        assert result.operation_type == OperationType.READ

    def test_denies_unknown_module(self) -> None:
        """验证未知模块被拒绝。"""
        pm = PermissionManager()
        result = pm.check_permission_detailed("unknown")
        assert result.allowed is False
        assert "不在白名单中" in result.reason

    def test_denies_execute_when_disabled(self) -> None:
        """验证执行工具在关闭时被拒绝。"""
        pm = PermissionManager()
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = False
            result = pm.check_permission_detailed("docker_restart")
            assert result.allowed is False
            assert result.operation_type == OperationType.EXECUTE
            assert "execute_tools_enabled=False" in result.reason
        finally:
            settings.execute_tools_enabled = original

    def test_allows_execute_when_enabled(self) -> None:
        """验证执行工具在开启时通过。"""
        pm = PermissionManager()
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = True
            result = pm.check_permission_detailed("docker_restart")
            assert result.allowed is True
            assert result.operation_type == OperationType.EXECUTE
            assert result.module_name == "docker"
        finally:
            settings.execute_tools_enabled = original

    def test_read_tool_passes_module_check(self) -> None:
        """验证只读工具（在已允许模块下）通过检查。"""
        pm = PermissionManager()
        # 装饰器传入的是模块名 "system"，不是工具名 "get_server_health"
        result = pm.check_permission_detailed("system")
        assert result.allowed is True
        assert result.operation_type == OperationType.READ
        # 再验证 docker_list 所在的 docker 模块
        result2 = pm.check_permission_detailed("docker")
        assert result2.allowed is True

    def test_with_security_context(self) -> None:
        """验证传递安全上下文。"""
        pm = PermissionManager()
        context = {"caller": "cursor", "request_id": "abc123"}
        result = pm.check_permission_detailed(
            "system", context=context,
        )
        assert result.security_context["caller"] == "cursor"
        assert result.security_context["request_id"] == "abc123"


class TestGetModuleName:
    """_get_module_name 方法测试。"""

    def test_module_name_docker(self) -> None:
        pm = PermissionManager()
        assert pm._get_module_name("docker_list") == "docker"
        assert pm._get_module_name("docker_logs") == "docker"
        assert pm._get_module_name("docker_restart") == "docker"

    def test_module_name_system(self) -> None:
        pm = PermissionManager()
        assert pm._get_module_name("get_server_health") == "get"
        # 工具名没有下划线时返回原名称
        assert pm._get_module_name("system") == "system"