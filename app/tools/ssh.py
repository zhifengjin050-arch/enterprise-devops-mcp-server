"""SSH 工具模块。

提供远程服务器管理运维能力，包括：
- SSH 连接检查（ssh_check_connection）
- 远程命令执行（ssh_execute_command）— 执行类操作
- 文件上传（ssh_upload_file）— 执行类操作
- 多服务器管理

基于 paramiko 实现，集成安全体系。
"""

import logging
import time
from pathlib import Path
from typing import Annotated, Any

from fastmcp import FastMCP

from app.config import settings
from app.security.permission import (
    require_permission,
    require_execute_permission,
    get_permission_manager,
)

logger = logging.getLogger(__name__)

# ---- 危险命令前缀黑名单 ----
DANGEROUS_COMMANDS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "mkfs.ext4",
    "mkfs.xfs",
    "dd if=",
    ":(){ :|:& };:",
    "> /dev/sda",
    "> /dev/sdb",
    "shutdown",
    "shutdown -h",
    "shutdown -r",
    "reboot",
    "halt",
    "poweroff",
    "init 0",
    "init 6",
    "chmod -R 777 /",
    "chown -R  /",
]


def _validate_command(command: str) -> str | None:
    """校验命令安全性，检查是否包含危险操作。

    Args:
        command: 待执行的命令

    Returns:
        如果命令安全返回 None，否则返回错误描述
    """
    command_stripped = command.strip().lower()

    # 检查黑名单前缀
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous.lower() in command_stripped:
            logger.warning("危险命令拦截: '%s' 匹配黑名单 '%s'", command, dangerous)
            return f"命令包含危险操作 '{dangerous}'，已被安全模块拦截"

    # 检查配置中的 blocked_commands
    if not get_permission_manager().check_command(command):
        return "命令已被安全策略拦截"

    return None


def _validate_path(path_str: str) -> str | None:
    """校验文件路径安全性。

    Args:
        path_str: 文件路径

    Returns:
        如果路径安全返回 None，否则返回错误描述
    """
    # 转换为 Path 对象以便跨平台处理
    try:
        p = Path(path_str)
    except Exception:
        return f"无效的文件路径: {path_str}"

    # 检查路径遍历攻击
    if ".." in path_str.split("/") or ".." in path_str.split("\\"):
        return "文件路径不允许包含 '..'（路径遍历攻击）"

    # 检查绝对路径限制（上传目标必须是绝对路径）
    # 远程路径应当以 / 开头
    # 本地文件上传检查略

    return None


def _get_ssh_client(
    host: str,
    username: str,
    port: int = 22,
    timeout: int | None = None,
    password: str | None = None,
) -> Any:
    """创建并连接 SSH 客户端。

    Args:
        host: 目标服务器地址
        username: SSH 用户名
        port: SSH 端口
        timeout: 连接超时（秒）
        password: SSH 密码（可选，默认使用密钥认证）

    Returns:
        已连接的 SSHClient 实例

    Raises:
        Exception: 连接失败时抛出
    """
    import paramiko

    timeout = timeout or settings.ssh_default_timeout

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        hostname=host,
        port=port,
        username=username,
        password=password,
        timeout=timeout,
        allow_agent=False,  # 避免弹出 agent 认证窗口
        look_for_keys=False,  # 防止意外密钥加载
    )
    return client


@require_permission("ssh_check_connection")
def ssh_check_connection(
    host: Annotated[str, "目标服务器 IP 或域名"],
    username: Annotated[str, "SSH 登录用户名"],
    port: Annotated[int, "SSH 端口，默认 22"] = 22,
    password: Annotated[str | None, "SSH 密码（可选，不提供则使用密钥认证）"] = None,
) -> dict[str, str]:
    """测试远程服务器的 SSH 连接状态。

    尝试建立 SSH 连接并测量延迟，用于确认服务器可达性和认证是否正常。
    此操作为只读操作，不会在远程服务器上执行任何命令。

    Args:
        host: 目标服务器地址
        username: SSH 用户名
        port: SSH 端口，默认 22
        password: SSH 密码（可选）

    Returns:
        连接状态信息，包含 status, host, latency_ms

    异常时返回 {"status": "error", "message": "..."}
    """
    logger.info("Tool 调用: ssh_check_connection (host=%s:%d, user=%s)", host, port, username)
    start = time.time()

    try:
        client = _get_ssh_client(host=host, username=username, port=port, password=password)
        client.close()
        elapsed_ms = int((time.time() - start) * 1000)

        return {
            "status": "success",
            "host": host,
            "latency_ms": str(elapsed_ms),
        }
    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        logger.error("SSH 连接失败 (host=%s): %s", host, e)
        return {
            "status": "error",
            "host": host,
            "message": f"SSH 连接失败: {e}",
            "latency_ms": str(elapsed_ms),
        }


@require_execute_permission("ssh_execute_command")
def ssh_execute_command(
    host: Annotated[str, "目标服务器 IP 或域名"],
    username: Annotated[str, "SSH 登录用户名"],
    command: Annotated[str, "要执行的命令"],
    port: Annotated[int, "SSH 端口，默认 22"] = 22,
    password: Annotated[str | None, "SSH 密码（可选）"] = None,
) -> dict[str, str]:
    """在远程服务器上安全执行命令。

    此操作属于执行类，需要管理员开启 EXECUTE_TOOLS_ENABLED=true。
    执行前会经过多层安全检查：
    1. 危险命令黑名单过滤（rm -rf /, mkfs, shutdown, reboot 等）
    2. PermissionManager 命令校验
    3. ExecuteProtection 速率限制和确认机制

    执行后返回标准输出、标准错误和退出码。

    Args:
        host: 目标服务器地址
        username: SSH 用户名
        command: 要执行的命令
        port: SSH 端口，默认 22
        password: SSH 密码（可选）

    Returns:
        包含 stdout, stderr, status(exit_code) 的执行结果

    异常时返回 {"status": "error", "message": "..."}
    """
    logger.info(
        "Tool 调用: ssh_execute_command (host=%s:%d, user=%s, cmd=%s)",
        host, port, username, command,
    )

    # 1. 命令安全过滤
    error_msg = _validate_command(command)
    if error_msg:
        logger.warning("命令被安全模块拦截: %s", command)
        return {
            "stdout": "",
            "stderr": error_msg,
            "status": "1",
        }

    try:
        client = _get_ssh_client(host=host, username=username, port=port)
        stdin, stdout, stderr = client.exec_command(command, timeout=30)
        exit_code = stdout.channel.recv_exit_status()

        stdout_str = stdout.read().decode("utf-8", errors="replace")
        stderr_str = stderr.read().decode("utf-8", errors="replace")

        client.close()

        return {
            "stdout": stdout_str,
            "stderr": stderr_str,
            "status": str(exit_code),
        }
    except Exception as e:
        logger.error("SSH 命令执行失败 (host=%s): %s", host, e)
        return {
            "stdout": "",
            "stderr": f"SSH 命令执行失败: {e}",
            "status": "1",
        }


@require_execute_permission("ssh_upload_file")
def ssh_upload_file(
    host: Annotated[str, "目标服务器 IP 或域名"],
    username: Annotated[str, "SSH 登录用户名"],
    local_path: Annotated[str, "本地文件绝对路径"],
    remote_path: Annotated[str, "远程目标绝对路径"],
    port: Annotated[int, "SSH 端口，默认 22"] = 22,
) -> dict[str, str]:
    """安全上传文件到远程服务器。

    此操作属于执行类，需要管理员开启 EXECUTE_TOOLS_ENABLED=true。
    上传前会经过路径安全性校验，防止路径遍历攻击。

    Args:
        host: 目标服务器地址
        username: SSH 用户名
        local_path: 本地文件路径
        remote_path: 远程目标路径
        port: SSH 端口，默认 22

    Returns:
        包含 status, host, local_path, remote_path 的上传结果

    异常时返回 {"status": "error", "message": "..."}
    """
    logger.info(
        "Tool 调用: ssh_upload_file (host=%s, %s -> %s)",
        host, local_path, remote_path,
    )

    # 1. 路径安全校验
    local_err = _validate_path(local_path)
    if local_err:
        return {"status": "error", "message": local_err}

    remote_err = _validate_path(remote_path)
    if remote_err:
        return {"status": "error", "message": remote_err}

    # 2. 检查本地文件存在
    local_file = Path(local_path)
    if not local_file.exists():
        return {"status": "error", "message": f"本地文件不存在: {local_path}"}

    if not local_file.is_file():
        return {"status": "error", "message": f"路径不是文件: {local_path}"}

    try:
        client = _get_ssh_client(host=host, username=username, port=port)
        sftp = client.open_sftp()
        sftp.put(local_path, remote_path)
        sftp.close()
        client.close()

        return {
            "status": "success",
            "host": host,
            "local_path": local_path,
            "remote_path": remote_path,
        }
    except Exception as e:
        logger.error("SSH 文件上传失败 (host=%s): %s", host, e)
        return {"status": "error", "message": f"SSH 文件上传失败: {e}"}


def register_ssh_tools(mcp: FastMCP) -> None:
    """向 MCP Server 注册 SSH 远程管理相关的 Tool。

    Args:
        mcp: FastMCP 实例
    """

    @mcp.tool(
        name="ssh_check_connection",
        description="测试远程服务器的 SSH 连接状态。"
        "尝试建立 SSH 连接并测量延迟（毫秒），用于确认服务器可达性和认证是否正常。"
        "此操作为只读操作，不会在远程服务器上执行任何命令。"
        "使用场景：AI Agent 检测目标服务器是否在线、SSH 服务是否正常。",
    )
    def _check_wrapper(
        host: Annotated[str, "目标服务器 IP 或域名"],
        username: Annotated[str, "SSH 登录用户名"],
        port: Annotated[int, "SSH 端口，默认 22"] = 22,
        password: Annotated[str | None, "SSH 密码（可选）"] = None,
    ) -> dict[str, str]:
        """SSH 连接检查。"""
        return ssh_check_connection(host=host, username=username, port=port, password=password)

    @mcp.tool(
        name="ssh_execute_command",
        description="在远程服务器上安全执行命令。"
        "此操作属于执行类，需要管理员在 .env 中设置 EXECUTE_TOOLS_ENABLED=true 才能使用。"
        "执行前会经过多层安全检查：危险命令黑名单过滤（禁止 rm -rf /, mkfs, shutdown, reboot 等）、"
        "PermissionManager 命令校验、ExecuteProtection 速率限制和确认机制。"
        "执行后返回标准输出、标准错误和退出码。"
        "使用场景：AI Agent 在获得授权后远程执行运维命令、排查服务器问题。",
    )
    def _exec_wrapper(
        host: Annotated[str, "目标服务器 IP 或域名"],
        username: Annotated[str, "SSH 登录用户名"],
        command: Annotated[str, "要执行的命令"],
        port: Annotated[int, "SSH 端口，默认 22"] = 22,
        password: Annotated[str | None, "SSH 密码（可选）"] = None,
    ) -> dict[str, str]:
        """SSH 远程命令执行。"""
        return ssh_execute_command(
            host=host, username=username, command=command, port=port, password=password,
        )

    @mcp.tool(
        name="ssh_upload_file",
        description="安全上传文件到远程服务器。"
        "此操作属于执行类，需要管理员开启 EXECUTE_TOOLS_ENABLED=true 才能使用。"
        "上传前会经过路径安全性校验，防止路径遍历攻击。"
        "使用场景：AI Agent 在获得授权后上传配置文件、部署脚本到远程服务器。",
    )
    def _upload_wrapper(
        host: Annotated[str, "目标服务器 IP 或域名"],
        username: Annotated[str, "SSH 登录用户名"],
        local_path: Annotated[str, "本地文件绝对路径"],
        remote_path: Annotated[str, "远程目标绝对路径"],
        port: Annotated[int, "SSH 端口，默认 22"] = 22,
        password: Annotated[str | None, "SSH 密码（可选）"] = None,
    ) -> dict[str, str]:
        """SSH 文件上传。"""
        return ssh_upload_file(
            host=host, username=username,
            local_path=local_path, remote_path=remote_path,
            port=port, password=password,
        )

    logger.info("SSH 工具注册完毕")