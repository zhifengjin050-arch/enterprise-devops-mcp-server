"""配置管理模块。

使用 pydantic-settings 管理所有服务配置，支持环境变量和 .env 文件读取。
"""

import json
from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """企业级 DevOps MCP Server 全局配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ---- 基础信息 ----
    mcp_server_name: str = "Enterprise DevOps MCP Server"
    mcp_server_version: str = "1.0.1"

    # ---- API / 安全 ----
    api_key: str = ""
    enable_security: bool = True

    # ---- 工具白名单（逗号分隔） ----
    allowed_tools: str = "system,docker,kubernetes,ssh"

    # ---- 危险命令黑名单（逗号分隔） ----
    blocked_commands: str = "rm -rf,shutdown,reboot,dd if,mkfs"

    # ---- Docker 配置 ----
    docker_host: str = "unix:///var/run/docker.sock"
    docker_tls_verify: bool = False
    docker_cert_path: str = ""

    # ---- Kubernetes 配置 ----
    k8s_enabled: bool = True
    """是否启用 Kubernetes Tool 模块。"""

    k8s_kubeconfig_path: str = ""
    """Kubeconfig 文件路径，为空时自动使用默认路径 (~/.kube/config)。"""

    k8s_namespace: str = "default"
    """默认 Kubernetes 命名空间。"""

    # ---- SSH 默认配置 ----
    ssh_default_port: int = 22
    ssh_default_timeout: int = 30

    ssh_servers: str = ""
    """
    多服务器配置（JSON 格式字符串）。
    示例:
    [{"name":"example-server","host":"YOUR_SERVER_IP","port":22,"username":"YOUR_USERNAME"}]
    注意：不要在此保存密码明文，SSH 认证建议使用密钥。
    """

    # ---- 执行权限 ----
    execute_tools_enabled: bool = False
    """是否启用执行类操作。默认关闭，需要管理员手动开启。"""

    # ---- 只读工具列表（逗号分隔） ----
    read_only_tools: str = (
        "get_server_health,docker_list,docker_logs,"
        "k8s_get_pods,k8s_get_deployments,k8s_get_services,k8s_logs,"
        "ssh_check_connection"
    )
    """只读工具始终可用，无需额外权限。"""

    # ---- 执行工具列表（逗号分隔） ----
    execute_tools: str = "docker_restart,ssh_execute_command,ssh_upload_file"
    """执行类工具，需要 execute_tools_enabled=True 才能使用。"""

    # ---- 执行安全保护 ----
    execute_protection_level: str = "basic"
    """执行保护等级: off / basic / strict。"""

    execute_max_calls_per_minute: int = 10
    """每分钟最大执行调用次数（仅 basic / strict 模式生效）。"""

    # ---- 审计日志 ----
    audit_log_enabled: bool = True
    """是否启用审计日志记录。"""

    audit_log_max_entries: int = 1000
    """审计日志最大条目数（环形缓冲区防止内存溢出）。"""

    # ---- 日志 ----
    log_level: str = "INFO"

    def get_allowed_tools_list(self) -> list[str]:
        """解析工具白名单。"""
        return [t.strip() for t in self.allowed_tools.split(",") if t.strip()]

    def get_blocked_commands_list(self) -> list[str]:
        """解析危险命令黑名单。"""
        return [c.strip() for c in self.blocked_commands.split(",") if c.strip()]

    def get_read_only_tools_list(self) -> list[str]:
        """解析只读工具列表。"""
        return [t.strip() for t in self.read_only_tools.split(",") if t.strip()]

    def get_execute_tools_list(self) -> list[str]:
        """解析执行工具列表。"""
        return [t.strip() for t in self.execute_tools.split(",") if t.strip()]

    def get_ssh_servers(self) -> list[dict[str, Any]]:
        """解析 SSH 多服务器配置。

        Returns:
            服务器配置列表，每个元素包含 name, host, port, username
        """
        if not self.ssh_servers:
            return []
        try:
            servers = json.loads(self.ssh_servers)
            if isinstance(servers, list):
                return servers
            return []
        except (json.JSONDecodeError, TypeError):
            return []


settings = Settings()