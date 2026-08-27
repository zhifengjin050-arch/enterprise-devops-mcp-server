"""Docker 工具模块。

提供容器管理运维能力，包括：
- Docker 容器列表（docker_list）
- 容器日志查询（docker_logs）
- 容器安全重启（docker_restart）

基于 docker SDK for Python 实现。
"""

import logging
from typing import Annotated, Any

import docker
from docker.errors import DockerException, NotFound, APIError
from fastmcp import FastMCP

from app.security.permission import (
    require_permission,
    require_execute_permission,
)

logger = logging.getLogger(__name__)


def _get_docker_client() -> docker.DockerClient:
    """初始化 Docker 客户端。

    Returns:
        DockerClient 实例

    Raises:
        DockerException: Docker 服务未运行或连接失败
    """
    return docker.from_env()


def _parse_ports(container: docker.models.containers.Container) -> str:
    """将容器端口映射解析为可读字符串。

    Args:
        container: Docker 容器对象

    Returns:
        端口映射字符串，如 "80:80/tcp, 443:443/tcp"
    """
    port_mappings = container.ports
    if not port_mappings:
        return "-"

    parts: list[str] = []
    for container_port, host_bindings in port_mappings.items():
        if host_bindings:
            for binding in host_bindings:
                host_port = binding.get("HostPort", "-")
                parts.append(f"{host_port}:{container_port}")
        else:
            parts.append(f"-:{container_port}")

    return ", ".join(parts)


def _get_container_list(
    client: docker.DockerClient,
    all_containers: bool = False,
) -> list[dict[str, str]]:
    """获取容器列表。

    Args:
        client: DockerClient 实例
        all_containers: 是否包含已停止的容器

    Returns:
        容器信息列表，每个元素包含 name, image, status, ports
    """
    containers = client.containers.list(all=all_containers)
    result: list[dict[str, str]] = []

    for container in sorted(containers, key=lambda c: c.name or ""):
        # 容器可能没有 name（自动生成的名称）
        container_name = container.name or container.short_id

        # 解析镜像名称
        image_name = "-"
        if container.image:
            image_name = (
                container.image.tags[0]
                if container.image.tags
                else container.image.short_id
            )

        result.append({
            "name": container_name,
            "image": image_name,
            "status": container.status,
            "ports": _parse_ports(container),
        })

    return result


@require_permission("docker")
def docker_list(all_containers: bool = False) -> list[dict[str, str]]:
    """获取当前 Docker 主机上所有容器的状态列表。

    Args:
        all_containers: 是否包含已停止的容器，默认只显示运行中的容器

    Returns:
        容器信息 JSON 数组，每个元素包含 name, image, status, ports

    异常时返回 [{"status": "error", "message": "..."}]
    """
    logger.info("Tool 调用: docker_list (all=%s)", all_containers)
    try:
        client = _get_docker_client()
        return _get_container_list(client, all_containers)
    except DockerException as e:
        logger.error("Docker 连接失败: %s", e)
        return [{"status": "error", "message": f"Docker 服务连接失败: {e}"}]
    except APIError as e:
        logger.error("Docker API 错误: %s", e)
        return [{"status": "error", "message": f"Docker API 错误: {e}"}]


@require_permission("docker")
def docker_logs(
    container_name: Annotated[str, "容器名称或 ID"],
    lines: Annotated[int, "返回日志的行数，默认 100"] = 100,
) -> dict[str, str]:
    """获取指定 Docker 容器的日志。

    Args:
        container_name: 容器名称或 ID
        lines: 返回日志的行数

    Returns:
        包含 container 和 logs 字段的字典

    异常时返回 {"status": "error", "message": "..."}
    """
    logger.info("Tool 调用: docker_logs (container=%s, lines=%d)", container_name, lines)
    lines = max(1, min(int(lines or 100), 1000))
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        log_bytes = container.logs(tail=lines, timestamps=False)
        log_text = log_bytes.decode("utf-8", errors="replace") if log_bytes else ""

        return {
            "container": container_name,
            "logs": log_text,
        }
    except NotFound:
        logger.warning("容器未找到: %s", container_name)
        return {"status": "error", "message": f"容器 '{container_name}' 不存在"}
    except DockerException as e:
        logger.error("Docker 连接失败: %s", e)
        return {"status": "error", "message": f"Docker 服务连接失败: {e}"}
    except APIError as e:
        logger.error("Docker API 错误: %s", e)
        return {"status": "error", "message": f"Docker API 错误: {e}"}


@require_execute_permission("docker_restart")
def docker_restart(
    container_name: Annotated[str, "需要重启的容器名称或 ID"],
) -> dict[str, str]:
    """安全重启指定的 Docker 容器。

    此操作会先检查权限，确认后才执行容器重启。
    属于执行类操作，需要额外的执行权限配置。

    Args:
        container_name: 容器名称或 ID

    Returns:
        包含 container, action, status 字段的字典

    异常时返回 {"status": "error", "message": "..."}
    """
    logger.info("Tool 调用: docker_restart (container=%s)", container_name)
    try:
        client = _get_docker_client()
        container = client.containers.get(container_name)
        container.restart(timeout=10)
        logger.info("容器重启成功: %s", container_name)
        return {
            "container": container_name,
            "action": "restart",
            "status": "success",
        }
    except NotFound:
        logger.warning("容器未找到: %s", container_name)
        return {"status": "error", "message": f"容器 '{container_name}' 不存在"}
    except DockerException as e:
        logger.error("Docker 连接失败: %s", e)
        return {"status": "error", "message": f"Docker 服务连接失败: {e}"}
    except APIError as e:
        logger.error("Docker API 错误: %s", e)
        return {"status": "error", "message": f"Docker API 错误: {e}"}


def register_docker_tools(mcp: FastMCP) -> None:
    """向 MCP Server 注册 Docker 管理相关的 Tool。

    Args:
        mcp: FastMCP 实例
    """

    @mcp.tool(
        name="docker_list",
        description="获取当前服务器上所有 Docker 容器的运行状态列表，包括容器名称、使用的镜像、运行状态（running/exited）和端口映射信息。"
        "用于 AI Agent 查看 Docker 服务部署情况、巡检容器健康状态、排查哪些服务在运行。"
        "参数 all_containers=True 时可同时查看已停止的容器。",
    )
    def _list_wrapper(
        all_containers: Annotated[bool, "是否包含已停止的容器，默认 False 只显示运行中的容器"] = False,
    ) -> list[dict[str, str]]:
        """获取 Docker 容器列表。"""
        return docker_list(all_containers=all_containers)

    @mcp.tool(
        name="docker_logs",
        description="获取指定 Docker 容器的运行日志，用于 AI Agent 排查容器异常、分析应用错误。"
        "可通过 lines 参数控制返回的日志行数（默认返回最后 100 行）。"
        "使用场景：容器启动失败排查、应用错误分析、实时日志查看。",
    )
    def _logs_wrapper(
        container_name: Annotated[str, "容器名称或 ID，必填"],
        lines: Annotated[int, "返回日志的行数，默认 100，最大可设为 1000"] = 100,
    ) -> dict[str, str]:
        """获取 Docker 容器日志。"""
        return docker_logs(container_name=container_name, lines=lines)

    @mcp.tool(
        name="docker_restart",
        description="安全重启指定的 Docker 容器（timeout=10 秒）。"
        "此属于执行类操作，需要管理员在 .env 配置中设置 EXECUTE_TOOLS_ENABLED=true 才能使用。"
        "用于 AI Agent 在获得授权后重启出现故障的容器。"
        "注意：此操作会短暂中断服务，请确保有足够权限且了解影响范围后再调用。",
    )
    def _restart_wrapper(
        container_name: Annotated[str, "需要重启的容器名称或 ID，必填"],
    ) -> dict[str, str]:
        """安全重启 Docker 容器。"""
        return docker_restart(container_name=container_name)

    logger.info("Docker 工具注册完毕")