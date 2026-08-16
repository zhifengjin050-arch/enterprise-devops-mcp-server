"""Tool 注册模块。

统一管理所有 DevOps Tool 的注册逻辑，为后续扩展提供统一入口。
"""

import logging

from fastmcp import FastMCP

from app.config import settings
from app.security.permission import require_permission

logger = logging.getLogger(__name__)

# 已注册的 Tool 模块列表
_registered_modules: list[str] = []


def register_all_tools(mcp: FastMCP) -> None:
    """向 MCP Server 注册所有 DevOps Tool 模块。

    Args:
        mcp: FastMCP 实例
    """
    # ---- System Tools ----
    if "system" in settings.get_allowed_tools_list():
        from app.tools.system import register_system_tools

        register_system_tools(mcp)
        _registered_modules.append("system")
        logger.info("已注册 System 工具模块")

    # ---- Docker Tools ----
    if "docker" in settings.get_allowed_tools_list():
        from app.tools.docker import register_docker_tools

        register_docker_tools(mcp)
        _registered_modules.append("docker")
        logger.info("已注册 Docker 工具模块")

    # ---- Kubernetes Tools ----
    if "kubernetes" in settings.get_allowed_tools_list():
        from app.tools.kubernetes import register_kubernetes_tools

        register_kubernetes_tools(mcp)
        _registered_modules.append("kubernetes")
        logger.info("已注册 Kubernetes 工具模块")

    # ---- SSH Tools ----
    if "ssh" in settings.get_allowed_tools_list():
        from app.tools.ssh import register_ssh_tools

        register_ssh_tools(mcp)
        _registered_modules.append("ssh")
        logger.info("已注册 SSH 工具模块")


def get_registered_modules() -> list[str]:
    """获取已注册的模块列表。"""
    return _registered_modules.copy()