"""Tool Metadata overlay — 不修改既有工具执行逻辑。

供 MCP Client / Agent 做安全决策：风险等级、权限、是否审计。
"""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass(frozen=True)
class ToolMetadata:
    name: str
    description: str
    category: str
    risk_level: str
    required_permission: str
    audit_required: bool

    def to_dict(self) -> dict:
        return asdict(self)


TOOL_METADATA: dict[str, ToolMetadata] = {
    "get_server_health": ToolMetadata("get_server_health", "服务器健康检查", "system", "safe", "devops.viewer", False),
    "get_system_info": ToolMetadata("get_system_info", "系统信息", "system", "safe", "devops.viewer", False),
    "get_cpu_usage": ToolMetadata("get_cpu_usage", "CPU 使用率", "system", "safe", "devops.viewer", False),
    "get_memory_usage": ToolMetadata("get_memory_usage", "内存使用率", "system", "safe", "devops.viewer", False),
    "get_disk_usage": ToolMetadata("get_disk_usage", "磁盘使用率", "system", "safe", "devops.viewer", False),
    "get_audit_logs": ToolMetadata("get_audit_logs", "审计日志", "system", "moderate", "devops.admin", True),
    "list_processes": ToolMetadata("list_processes", "进程列表", "system", "safe", "devops.viewer", False),
    "docker_list": ToolMetadata("docker_list", "容器列表", "docker", "safe", "devops.viewer", False),
    "docker_logs": ToolMetadata("docker_logs", "容器日志", "docker", "safe", "devops.viewer", False),
    "docker_restart": ToolMetadata("docker_restart", "重启容器", "docker", "dangerous", "devops.admin", True),
    "k8s_get_pods": ToolMetadata("k8s_get_pods", "Pod 列表", "kubernetes", "safe", "devops.viewer", False),
    "k8s_get_deployments": ToolMetadata("k8s_get_deployments", "Deployment 列表", "kubernetes", "safe", "devops.viewer", False),
    "k8s_get_services": ToolMetadata("k8s_get_services", "Service 列表", "kubernetes", "safe", "devops.viewer", False),
    "k8s_logs": ToolMetadata("k8s_logs", "Pod 日志", "kubernetes", "safe", "devops.viewer", False),
    "ssh_check_connection": ToolMetadata("ssh_check_connection", "SSH 连通性", "ssh", "safe", "devops.viewer", False),
    "ssh_execute_command": ToolMetadata("ssh_execute_command", "SSH 执行命令", "ssh", "dangerous", "devops.admin", True),
    "ssh_upload_file": ToolMetadata("ssh_upload_file", "SSH 上传文件", "ssh", "dangerous", "devops.admin", True),
}


def get_tool_metadata(name: str) -> ToolMetadata | None:
    return TOOL_METADATA.get(name)


def list_tool_metadata() -> list[dict]:
    return [m.to_dict() for m in TOOL_METADATA.values()]
