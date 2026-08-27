"""System 工具模块。

提供服务器系统层面的运维能力，包括：
- CPU / 内存 / 磁盘监控（get_server_health）
- 系统信息查询（get_system_info）
- CPU 使用率详情（get_cpu_usage）
- 内存使用情况（get_memory_usage）
- 磁盘使用情况（get_disk_usage）
- 进程列表（list_processes）
- 审计日志查询（get_audit_logs）

基于 psutil 实现。
"""

import logging
import platform
import socket
from datetime import datetime, timezone
from typing import Annotated, Any

import psutil

from fastmcp import FastMCP

from app.security.permission import require_permission
from app.security.audit import get_audit_logger

logger = logging.getLogger(__name__)

# ---- 健康阈值 ----
_HEALTHY_THRESHOLD = 80.0
_CRITICAL_THRESHOLD = 95.0


def _determine_health_status(
    cpu: float,
    memory: float,
    disk: float,
) -> str:
    """根据指标判断系统健康状态。

    Args:
        cpu: CPU 使用率百分比
        memory: 内存使用率百分比
        disk: 磁盘使用率百分比

    Returns:
        "healthy" | "warning" | "critical"
    """
    values = [cpu, memory, disk]
    if any(v >= _CRITICAL_THRESHOLD for v in values):
        return "critical"
    if any(v >= _HEALTHY_THRESHOLD for v in values):
        return "warning"
    return "healthy"


def _format_uptime(boot_time: float) -> str:
    """将启动时间戳格式化为可读的运行时长。

    Args:
        boot_time: 系统启动时间戳（秒）

    Returns:
        可读的运行时长字符串，如 "10 days, 3 hours"
    """
    uptime_seconds = datetime.now(tz=timezone.utc).timestamp() - boot_time

    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)

    parts: list[str] = []
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0 or not parts:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

    return ", ".join(parts)


def _collect_server_health() -> dict[str, Any]:
    """采集服务器实时健康数据。

    Returns:
        包含 hostname, cpu_usage, memory_usage, disk_usage, uptime, status 的字典

    Raises:
        psutil.Error: psutil 调用异常
        OSError: 系统调用异常
    """
    hostname = socket.gethostname()
    cpu_usage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    memory_usage = memory.percent
    disk = psutil.disk_usage("/")
    disk_usage = disk.percent
    boot_time = psutil.boot_time()
    uptime = _format_uptime(boot_time)
    status = _determine_health_status(cpu_usage, memory_usage, disk_usage)

    return {
        "hostname": hostname,
        "cpu_usage": round(cpu_usage, 1),
        "memory_usage": round(memory_usage, 1),
        "disk_usage": round(disk_usage, 1),
        "uptime": uptime,
        "status": status,
    }


def _collect_system_info() -> dict[str, str]:
    """采集系统基本信息。

    Returns:
        包含 hostname, os, platform, python_version, uptime 的字典
    """
    boot_time = psutil.boot_time()
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "uptime": _format_uptime(boot_time),
    }


def _collect_cpu_usage() -> dict[str, Any]:
    """采集 CPU 使用率详情。

    Returns:
        包含 cpu_percent, cpu_count 的字典
    """
    return {
        "cpu_percent": round(psutil.cpu_percent(interval=0.5), 1),
        "cpu_count": psutil.cpu_count(),
    }


def _collect_memory_usage() -> dict[str, Any]:
    """采集内存使用情况。

    Returns:
        包含 total, used, available, percent 的字典（字节数）
    """
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "used": memory.used,
        "available": memory.available,
        "percent": memory.percent,
    }


def _collect_disk_usage() -> list[dict[str, Any]]:
    """采集所有分区的磁盘使用情况。

    Returns:
        每个分区包含 path, total, used, free, percent 的列表
    """
    result: list[dict[str, Any]] = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            result.append({
                "path": part.mountpoint,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent,
            })
        except PermissionError:
            continue
    return result


def _collect_processes(limit: int = 10) -> list[dict[str, Any]]:
    """采集进程列表（按 CPU 使用率降序排列）。

    Args:
        limit: 返回的进程数量上限

    Returns:
        每个进程包含 pid, name, cpu_percent, memory_percent 的列表
    """
    processes: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            pinfo = proc.info
            processes.append({
                "pid": pinfo["pid"],
                "name": pinfo["name"] or "",
                "cpu_percent": round(pinfo["cpu_percent"] or 0.0, 1),
                "memory_percent": round(pinfo["memory_percent"] or 0.0, 1),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    processes.sort(key=lambda p: p["cpu_percent"], reverse=True)
    return processes[:limit]


@require_permission("system")
def get_server_health() -> dict[str, Any]:
    """获取当前服务器健康状态。

    AI Agent 可通过此 Tool 快速了解服务器运行概况：
    - CPU、内存、磁盘使用率
    - 系统运行时长
    - 整体健康等级判定（healthy / warning / critical）

    Returns:
        结构化服务器数据：hostname, cpu_usage, memory_usage,
        disk_usage, uptime, status

    异常时返回 {"status": "error", "message": "<描述>"}
    """
    logger.info("Tool 调用: get_server_health")
    try:
        return _collect_server_health()
    except (psutil.Error, OSError) as e:
        logger.error("服务器健康检查失败: %s", e)
        return {
            "status": "error",
            "message": f"获取服务器健康信息失败: {e}",
        }


@require_permission("system")
def get_system_info() -> dict[str, str]:
    """获取当前服务器系统基本信息。

    返回主机名、操作系统类型、平台详情、Python 版本和系统运行时长。
    用于 AI Agent 了解服务器基础环境信息。

    Returns:
        包含 hostname, os, platform, python_version, uptime 的字典

    异常时返回 {"status": "error", "message": "..."}
    """
    logger.info("Tool 调用: get_system_info")
    try:
        return _collect_system_info()
    except Exception as e:
        logger.error("系统信息获取失败: %s", e)
        return {"status": "error", "message": f"获取系统信息失败: {e}"}


@require_permission("system")
def get_cpu_usage() -> dict[str, Any]:
    """获取 CPU 使用率详情。

    返回整体 CPU 使用率百分比和逻辑 CPU 核心数。
    用于 AI Agent 分析 CPU 性能瓶颈。

    Returns:
        包含 cpu_percent, cpu_count 的字典

    异常时返回 {"status": "error", "message": "..."}
    """
    logger.info("Tool 调用: get_cpu_usage")
    try:
        return _collect_cpu_usage()
    except Exception as e:
        logger.error("CPU 信息获取失败: %s", e)
        return {"status": "error", "message": f"获取 CPU 信息失败: {e}"}


@require_permission("system")
def get_memory_usage() -> dict[str, Any]:
    """获取内存使用情况。

    返回总内存、已用内存、可用内存（字节数）和使用百分比。
    用于 AI Agent 分析内存瓶颈。

    Returns:
        包含 total, used, available, percent 的字典

    异常时返回 {"status": "error", "message": "..."}
    """
    logger.info("Tool 调用: get_memory_usage")
    try:
        return _collect_memory_usage()
    except Exception as e:
        logger.error("内存信息获取失败: %s", e)
        return {"status": "error", "message": f"获取内存信息失败: {e}"}


@require_permission("system")
def get_disk_usage() -> list[dict[str, Any]]:
    """获取所有分区的磁盘使用情况。

    返回每个文件系统的挂载点、总容量、已用空间、可用空间（字节数）和使用百分比。
    用于 AI Agent 分析磁盘空间瓶颈。

    Returns:
        每个分区包含 path, total, used, free, percent 的列表

    异常时返回 [{"status": "error", "message": "..."}]
    """
    logger.info("Tool 调用: get_disk_usage")
    try:
        return _collect_disk_usage()
    except Exception as e:
        logger.error("磁盘信息获取失败: %s", e)
        return [{"status": "error", "message": f"获取磁盘信息失败: {e}"}]


@require_permission("system")
def get_audit_logs(
    count: Annotated[int, "返回的日志条数，默认 20，最大 100"] = 20,
    tool_name: Annotated[str | None, "按工具名称过滤，可选"] = None,
    status: Annotated[str | None, "按执行状态过滤（success/error/permission_denied），可选"] = None,
) -> dict[str, Any]:
    """获取审计日志记录。

    返回最近的操作调用记录，包含调用时间、工具名、参数、权限结果、执行耗时等信息。
    可指定过滤条件。用于 AI Agent 了解操作历史和排查问题。

    Args:
        count: 返回的日志条数，默认 20，最大 100
        tool_name: 按工具名称过滤（可选）
        status: 按执行状态过滤（可选）

    Returns:
        包含 logs（日志列表）和 stats（统计信息）的字典

    异常时返回 {"status": "error", "message": "..."}
    """
    logger.info("Tool 调用: get_audit_logs (count=%d)", count)
    try:
        audit = get_audit_logger()
        # 限制最大返回条数
        count = min(max(count, 1), 100)
        logs = audit.get_recent_logs(count=count, tool_name=tool_name, status=status)
        stats = audit.get_stats()
        return {
            "logs": [log.to_dict() for log in logs],
            "stats": stats,
        }
    except Exception as e:
        logger.error("审计日志获取失败: %s", e)
        return {"status": "error", "message": "获取审计日志失败"}


_EXECUTE_CONFIRM_TOOLS = {
    "docker_restart",
    "ssh_execute_command",
    "ssh_upload_file",
}


@require_permission("system")
def confirm_execute_action(
    tool_name: Annotated[str, "要确认的执行类工具名"],
) -> dict[str, str]:
    """STRICT 模式下确认高危执行工具。"""
    name = (tool_name or "").strip()
    if name not in _EXECUTE_CONFIRM_TOOLS:
        return {
            "status": "error",
            "message": "只能确认 docker_restart / ssh_execute_command / ssh_upload_file",
        }
    from app.security.execute_protection import get_execute_protector

    get_execute_protector().confirm_action(name)
    return {"status": "success", "tool_name": name}


@require_permission("system")
def list_processes(
    limit: Annotated[int, "返回的进程数量上限，默认 10"] = 10,
) -> list[dict[str, Any]]:
    """列出当前服务器上按 CPU 使用率排序的进程。

    默认返回 CPU 使用率最高的 Top 10 进程，包含 PID、名称、CPU 和内存占用率。
    用于 AI Agent 排查异常进程或分析服务器负载。

    Args:
        limit: 返回的进程数量上限，默认 10

    Returns:
        每个进程包含 pid, name, cpu_percent, memory_percent 的列表

    异常时返回 [{"status": "error", "message": "..."}]
    """
    logger.info("Tool 调用: list_processes (limit=%d)", limit)
    try:
        return _collect_processes(limit=limit)
    except Exception as e:
        logger.error("进程列表获取失败: %s", e)
        return [{"status": "error", "message": f"获取进程列表失败: {e}"}]


def register_system_tools(mcp: FastMCP) -> None:
    """向 MCP Server 注册系统管理相关的 Tool。

    Args:
        mcp: FastMCP 实例
    """

    @mcp.tool(
        name="get_server_health",
        description="获取当前服务器 CPU、内存、磁盘和运行状态，用于 AI Agent 巡检服务器健康状况。"
        "返回健康等级：healthy（全部指标 < 80%）、warning（任一指标 >= 80%）、critical（任一指标 >= 95%）。"
        "异常时返回 error 状态。使用场景：服务器状态检查、故障排查前了解系统负载、定期巡检。",
    )
    def _health_wrapper() -> dict[str, Any]:
        """获取当前服务器健康状态。"""
        return get_server_health()

    @mcp.tool(
        name="get_system_info",
        description="获取服务器系统基本信息，包括主机名、操作系统类型、平台详情、Python 版本和系统运行时长。"
        "用于 AI Agent 了解服务器基础环境信息。",
    )
    def _system_info_wrapper() -> dict[str, str]:
        """获取服务器系统基本信息。"""
        return get_system_info()

    @mcp.tool(
        name="get_cpu_usage",
        description="获取 CPU 使用率详情，包括整体使用率和逻辑 CPU 核心数。"
        "用于 AI Agent 分析 CPU 性能瓶颈。",
    )
    def _cpu_wrapper() -> dict[str, Any]:
        """获取 CPU 使用率详情。"""
        return get_cpu_usage()

    @mcp.tool(
        name="get_memory_usage",
        description="获取内存使用情况，包括总内存、已用内存、可用内存（字节数）和使用百分比。"
        "用于 AI Agent 分析内存瓶颈。",
    )
    def _memory_wrapper() -> dict[str, Any]:
        """获取内存使用情况。"""
        return get_memory_usage()

    @mcp.tool(
        name="get_disk_usage",
        description="获取所有分区的磁盘使用情况，包括挂载点、总容量、已用/可用空间（字节数）和使用百分比。"
        "用于 AI Agent 分析磁盘空间瓶颈。",
    )
    def _disk_wrapper() -> list[dict[str, Any]]:
        """获取磁盘使用情况。"""
        return get_disk_usage()

    @mcp.tool(
        name="get_audit_logs",
        description="获取审计日志记录，包括最近的操作调用历史。支持按工具名称和执行状态过滤。"
        "返回每条日志的调用时间、工具名、参数、权限结果、执行状态和耗时。"
        "用于 AI Agent 审查操作历史、排查问题和安全审计。",
    )
    def _audit_wrapper(
        count: Annotated[int, "返回的日志条数，默认 20，最大 100"] = 20,
        tool_name: Annotated[str | None, "按工具名称过滤，可选"] = None,
        status: Annotated[str | None, "按执行状态过滤（success/error/permission_denied），可选"] = None,
    ) -> dict[str, Any]:
        """获取审计日志记录。"""
        return get_audit_logs(count=count, tool_name=tool_name, status=status)

    @mcp.tool(
        name="confirm_execute_action",
        description="在 EXECUTE_PROTECTION_LEVEL=strict 时，确认即将执行的高危工具。"
        "tool_name 必须是 docker_restart / ssh_execute_command / ssh_upload_file 之一。"
        "确认后该工具在本进程内可执行一次策略下的后续调用。",
    )
    def _confirm_wrapper(
        tool_name: Annotated[str, "要确认的执行类工具名"],
    ) -> dict[str, str]:
        """确认高危执行操作。"""
        return confirm_execute_action(tool_name=tool_name)

    @mcp.tool(
        name="list_processes",
        description="列出当前服务器上按 CPU 使用率降序排列的进程列表。"
        "默认返回 Top 10 进程，可通过 limit 参数控制数量。"
        "用于 AI Agent 排查异常进程或分析服务器负载。",
    )
    def _process_wrapper(
        limit: Annotated[int, "返回的进程数量上限，默认 10"] = 10,
    ) -> list[dict[str, Any]]:
        """列出当前运行进程。"""
        return list_processes(limit=limit)

    logger.info("System 工具注册完毕")