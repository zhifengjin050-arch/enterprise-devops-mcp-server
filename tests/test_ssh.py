"""SSH 工具模块测试。

测试 ssh_check_connection、ssh_execute_command、ssh_upload_file。
使用 mock 避免依赖真实 SSH 服务器。
"""

from unittest.mock import MagicMock, patch

import pytest

from app.tools.ssh import (
    ssh_check_connection,
    ssh_execute_command,
    ssh_upload_file,
    _validate_command,
    _validate_path,
    DANGEROUS_COMMANDS,
)

# 默认 execute_tools_enabled=False，因此需要手动开启才能测执行类操作（ssh_execute_command, ssh_upload_file）


def _enable_execute() -> None:
    """在测试中启用执行权限。"""
    from app.config import settings
    settings.execute_tools_enabled = True


def _disable_execute() -> None:
    """测试后恢复执行权限为关闭。"""
    from app.config import settings
    settings.execute_tools_enabled = False


class TestValidateCommand:
    """命令安全过滤测试。"""

    def test_safe_command_allowed(self) -> None:
        """验证安全命令不拦截。"""
        error = _validate_command("ls -la /var/log")
        assert error is None

    def test_dangerous_rm_blocked(self) -> None:
        """验证 rm -rf / 被拦截。"""
        error = _validate_command("rm -rf /")
        assert error is not None
        assert "危险操作" in error

    def test_dangerous_shutdown_blocked(self) -> None:
        """验证 shutdown 被拦截。"""
        error = _validate_command("shutdown -h now")
        assert error is not None

    def test_dangerous_reboot_blocked(self) -> None:
        """验证 reboot 被拦截。"""
        error = _validate_command("reboot")
        assert error is not None

    def test_dangerous_mkfs_blocked(self) -> None:
        """验证 mkfs 被拦截。"""
        error = _validate_command("mkfs.ext4 /dev/sda1")
        assert error is not None

    def test_dangerous_dd_blocked(self) -> None:
        """验证 dd if= 被拦截。"""
        error = _validate_command("dd if=/dev/zero of=/dev/sda")
        assert error is not None

    def test_safe_command_with_prefix(self) -> None:
        """验证包含危险前缀关键字但不完整的安全命令不被拦截。"""
        error = _validate_command("rm file.txt")
        assert error is None

    def test_dangerous_list_comprehensive(self) -> None:
        """验证危险命令列表全面。"""
        dangerous_items = [
            "rm -rf /",
            ":(){ :|:& };:",
            "mkfs",
            "shutdown",
            "reboot",
        ]
        for item in dangerous_items:
            found = any(d in item.lower() for d in [d.lower() for d in DANGEROUS_COMMANDS])
            assert found, f"危险命令 '{item}' 未被 DANGEROUS_COMMANDS 覆盖"


class TestValidatePath:
    """路径安全校验测试。"""

    def test_valid_absolute_path(self) -> None:
        """验证合法的绝对路径通过校验。"""
        error = _validate_path("/valid/path/file.txt")
        assert error is None

    def test_path_traversal_blocked(self) -> None:
        """验证路径遍历（..）被拦截。"""
        error = _validate_path("/var/../../etc/passwd")
        assert error is not None
        assert "路径遍历" in error


class TestSshCheckConnection:
    """ssh_check_connection 测试。"""

    @patch("app.tools.ssh._get_ssh_client")
    def test_returns_expected_structure(self, mock_get_client: MagicMock) -> None:
        """验证返回结构。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = ssh_check_connection(host="192.168.1.1", username="admin", port=22)
        assert isinstance(result, dict)
        assert "status" in result
        assert "host" in result
        assert "latency_ms" in result

    @patch("app.tools.ssh._get_ssh_client")
    def test_success_status(self, mock_get_client: MagicMock) -> None:
        """验证连接成功时返回 success。"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        result = ssh_check_connection(host="192.168.1.1", username="admin")
        assert result["status"] == "success"
        assert result["host"] == "192.168.1.1"

    @patch("app.tools.ssh._get_ssh_client")
    def test_handles_connection_error(self, mock_get_client: MagicMock) -> None:
        """验证连接失败时返回 error。"""
        mock_get_client.side_effect = Exception("Connection refused")

        result = ssh_check_connection(host="192.168.1.1", username="admin")
        assert result["status"] == "error"
        assert "连接失败" in result["message"]

    def test_read_only_permission(self) -> None:
        """验证权限分类为 READ_ONLY。"""
        from app.security.permission import PermissionManager

        pm = PermissionManager()
        op_type = pm.classify_operation("ssh_check_connection")
        assert op_type.value == "read"


class TestSshExecuteCommand:
    """ssh_execute_command 测试。"""

    @patch("app.tools.ssh._get_ssh_client")
    def test_handles_dangerous_command(self, mock_get_client: MagicMock) -> None:
        """验证危险命令被拦截而不执行（直接测试命令过滤函数）。"""
        error = _validate_command("rm -rf /")
        assert error is not None
        mock_get_client.assert_not_called()

    @patch("app.tools.ssh._get_ssh_client")
    def test_returns_expected_structure(self, mock_get_client: MagicMock) -> None:
        """验证返回结构（需启用 EXECUTE 权限）。"""
        _enable_execute()

        mock_client = MagicMock()
        mock_channel = MagicMock()
        mock_channel.recv_exit_status.return_value = 0
        mock_stdout = MagicMock()
        mock_stdout.read.return_value = b"output"
        mock_stdout.channel = mock_channel
        mock_stderr = MagicMock()
        mock_stderr.read.return_value = b""

        mock_client.exec_command.return_value = (None, mock_stdout, mock_stderr)
        mock_get_client.return_value = mock_client

        result = ssh_execute_command(
            host="192.168.1.1",
            username="admin",
            command="ls -la",
        )
        assert isinstance(result, dict)
        assert "stdout" in result
        assert result["stdout"] == "output"
        assert "stderr" in result
        assert "status" in result

        _disable_execute()

    def test_execute_permission(self) -> None:
        """验证权限分类为 EXECUTE。"""
        from app.security.permission import PermissionManager

        pm = PermissionManager()
        op_type = pm.classify_operation("ssh_execute_command")
        assert op_type.value == "execute"


class TestSshUploadFile:
    """ssh_upload_file 测试。"""

    @patch("app.tools.ssh._get_ssh_client")
    def test_handles_nonexistent_local_file(self, mock_get_client: MagicMock) -> None:
        """验证本地文件不存在时返回错误（需启用 EXECUTE 权限）。"""
        _enable_execute()

        result = ssh_upload_file(
            host="192.168.1.1",
            username="admin",
            local_path="/nonexistent/file.txt",
            remote_path="/tmp/file.txt",
        )
        assert result["status"] == "error"
        assert "不存在" in result["message"]
        mock_get_client.assert_not_called()

        _disable_execute()

    @patch("app.tools.ssh._get_ssh_client")
    def test_handles_path_traversal(self, mock_get_client: MagicMock) -> None:
        """验证路径遍历被拦截（需启用 EXECUTE 权限）。"""
        _enable_execute()

        result = ssh_upload_file(
            host="192.168.1.1",
            username="admin",
            local_path="/safe/file.txt",
            remote_path="/var/../../etc/passwd",
        )
        assert result["status"] == "error"
        assert "路径遍历" in result["message"]
        mock_get_client.assert_not_called()

        _disable_execute()

    def test_execute_permission(self) -> None:
        """验证权限分类为 EXECUTE。"""
        from app.security.permission import PermissionManager

        pm = PermissionManager()
        op_type = pm.classify_operation("ssh_upload_file")
        assert op_type.value == "execute"


class TestSshPermission:
    """SSH 权限测试。"""

    def test_ssh_module_in_whitelist(self) -> None:
        """验证 SSH 在模块白名单中。"""
        from app.config import settings

        allowed = settings.get_allowed_tools_list()
        assert "ssh" in allowed

    def test_ssh_check_connection_is_read_only(self) -> None:
        """验证 ssh_check_connection 在只读列表中。"""
        from app.config import settings

        read_only = settings.get_read_only_tools_list()
        assert "ssh_check_connection" in read_only

    def test_ssh_execute_command_in_execute_list(self) -> None:
        """验证 ssh_execute_command 在执行列表中。"""
        from app.config import settings

        execute_tools = settings.get_execute_tools_list()
        assert "ssh_execute_command" in execute_tools

    def test_ssh_upload_file_in_execute_list(self) -> None:
        """验证 ssh_upload_file 在执行列表中。"""
        from app.config import settings

        execute_tools = settings.get_execute_tools_list()
        assert "ssh_upload_file" in execute_tools


class TestSshRegistration:
    """SSH 注册测试。"""

    def test_three_tools_registered(self) -> None:
        """验证注册了 3 个 Tool。"""
        import asyncio
        from fastmcp import FastMCP
        from app.tools.ssh import register_ssh_tools

        mcp = FastMCP("test")
        register_ssh_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 3

    def test_all_tool_names(self) -> None:
        """验证所有 Tool 名称正确。"""
        import asyncio
        from fastmcp import FastMCP
        from app.tools.ssh import register_ssh_tools

        mcp = FastMCP("test")
        register_ssh_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        names = [t.name for t in tools]
        assert "ssh_check_connection" in names
        assert "ssh_execute_command" in names
        assert "ssh_upload_file" in names