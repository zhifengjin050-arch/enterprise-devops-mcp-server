"""权限管理模块测试。

测试 permission.py 中的权限校验逻辑。
"""

import pytest

from app.security.permission import PermissionManager, require_permission


class TestPermissionManager:
    """PermissionManager 测试用例。"""

    def test_check_permission_when_enabled_and_allowed(self) -> None:
        """安全模式启用 + 白名单中 => 通过。"""
        pm = PermissionManager()
        # 通过 monkeypatch 方式验证核心逻辑
        assert pm.enabled is True
        assert pm.check_permission("system") is True

    def test_check_permission_when_not_in_whitelist(self) -> None:
        """安全模式启用 + 不在白名单中 => 拒绝。"""
        pm = PermissionManager()
        assert pm.check_permission("unknown_tool") is False

    def test_get_allowed_tools_returns_set(self) -> None:
        """验证 get_allowed_tools 返回 set 类型。"""
        pm = PermissionManager()
        tools = pm.get_allowed_tools()
        assert isinstance(tools, set)
        assert "system" in tools
        assert "docker" in tools

    def test_get_blocked_commands_returns_set(self) -> None:
        """验证 get_blocked_commands 返回 set 类型。"""
        pm = PermissionManager()
        commands = pm.get_blocked_commands()
        assert isinstance(commands, set)
        assert "rm -rf" in commands

    def test_check_command_blocks_dangerous(self) -> None:
        """验证危险命令被拦截。"""
        pm = PermissionManager()
        assert pm.check_command("rm -rf /") is False
        assert pm.check_command("shutdown now") is False

    def test_check_command_allows_safe(self) -> None:
        """验证安全命令通过检查。"""
        pm = PermissionManager()
        assert pm.check_command("ls -la") is True
        assert pm.check_command("docker ps") is True


class TestExecutePermission:
    """check_execute_permission 执行权限测试。"""

    def test_execute_allowed_when_enabled(self) -> None:
        """execute_tools_enabled=True + 工具在列表中 => 通过。"""
        from app.config import settings
        pm = PermissionManager()
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = True
            assert pm.check_execute_permission("docker_restart") is True
        finally:
            settings.execute_tools_enabled = original

    def test_execute_denied_when_disabled(self) -> None:
        """execute_tools_enabled=False => 拒绝。"""
        from app.config import settings
        pm = PermissionManager()
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = False
            assert pm.check_execute_permission("docker_restart") is False
        finally:
            settings.execute_tools_enabled = original

    def test_execute_denied_when_module_not_in_whitelist(self) -> None:
        """工具模块不在白名单中 => 拒绝。"""
        from app.config import settings
        pm = PermissionManager()
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = True
            assert pm.check_execute_permission("unknown_restart") is False
        finally:
            settings.execute_tools_enabled = original

    def test_execute_denied_when_tool_not_in_list(self) -> None:
        """工具不在执行工具列表中 => 拒绝。"""
        from app.config import settings
        pm = PermissionManager()
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = True
            assert pm.check_execute_permission("system_reboot") is False
        finally:
            settings.execute_tools_enabled = original

    def test_get_module_name_splits_properly(self) -> None:
        """验证 _get_module_name 正确提取模块名。"""
        pm = PermissionManager()
        assert pm._get_module_name("docker_restart") == "docker"
        assert pm._get_module_name("system_info") == "system"

    def test_get_module_name_returns_full_name_if_no_underscore(self) -> None:
        """没有下划线的工具名直接返回原名称。"""
        pm = PermissionManager()
        assert pm._get_module_name("system") == "system"

    def test_get_read_only_tools(self) -> None:
        """验证只读工具列表返回 set。"""
        pm = PermissionManager()
        tools = pm.get_read_only_tools()
        assert isinstance(tools, set)
        assert "get_server_health" in tools
        assert "docker_list" in tools
        assert "docker_logs" in tools

    def test_get_execute_tools(self) -> None:
        """验证执行工具列表返回 set。"""
        pm = PermissionManager()
        tools = pm.get_execute_tools()
        assert isinstance(tools, set)
        assert "docker_restart" in tools

    def test_execute_enabled_property(self) -> None:
        """验证 execute_enabled 属性。"""
        from app.config import settings
        pm = PermissionManager()
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = True
            assert pm.execute_enabled is True
            settings.execute_tools_enabled = False
            assert pm.execute_enabled is False
        finally:
            settings.execute_tools_enabled = original


class TestRequirePermissionDecorator:
    """require_permission 装饰器测试。"""

    def test_decorator_allows_whitelisted_tool(self) -> None:
        """白名单中的 Tool 应正常执行。"""

        @require_permission("system")
        def safe_tool() -> dict[str, str]:
            return {"status": "ok"}

        result = safe_tool()
        assert result == {"status": "ok"}

    def test_decorator_blocks_unknown_tool(self) -> None:
        """不在白名单中的 Tool 应返回权限拒绝。"""

        @require_permission("unknown_tool")
        def blocked_tool() -> dict[str, str]:
            return {"status": "ok"}

        result = blocked_tool()
        assert result["error"] == "permission_denied"


class TestRequireExecutePermissionDecorator:
    """require_execute_permission 装饰器测试。"""

    def test_decorator_allows_when_enabled(self) -> None:
        """执行权限开启时，装饰器应放行。"""
        from app.config import settings
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = True
            from app.security.permission import require_execute_permission

            @require_execute_permission("docker_restart")
            def restart_tool() -> dict[str, str]:
                return {"status": "success"}

            result = restart_tool()
            assert result == {"status": "success"}
        finally:
            settings.execute_tools_enabled = original

    def test_decorator_blocks_when_disabled(self) -> None:
        """执行权限关闭时，装饰器应返回权限拒绝。"""
        from app.config import settings
        original = settings.execute_tools_enabled
        try:
            settings.execute_tools_enabled = False
            from app.security.permission import require_execute_permission

            @require_execute_permission("docker_restart")
            def restart_tool() -> dict[str, str]:
                return {"status": "success"}

            result = restart_tool()
            assert result["error"] == "execute_permission_denied"
        finally:
            settings.execute_tools_enabled = original