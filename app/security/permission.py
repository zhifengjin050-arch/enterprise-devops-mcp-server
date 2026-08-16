"""权限管理模块。

实现 Tool 级别的权限校验，支持：
- Tool 白名单检查
- 危险命令拦截
- 读写权限分类（只读 Tool vs 执行 Tool）
- 操作类型分类（READ / EXECUTE）
- 安全上下文追踪
- 结构化权限结果
- 权限装饰器
"""

import enum
import functools
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


class OperationType(str, enum.Enum):
    """操作类型分类。"""

    READ = "read"
    """只读操作——不会修改系统状态（如查询、查看日志）"""

    EXECUTE = "execute"
    """执行操作——会修改系统状态（如重启、删除、写入）"""


@dataclass
class PermissionResult:
    """权限校验结果（结构化详细结果）。"""

    allowed: bool
    """是否允许"""

    operation_type: OperationType | None = None
    """操作类型"""

    reason: str = ""
    """拒绝原因（allowed=True 时为空）"""

    module_name: str = ""
    """所属模块名称"""

    tool_name: str = ""
    """工具名称"""

    security_context: dict[str, str] = field(default_factory=dict)
    """安全上下文信息"""


class PermissionManager:
    """企业级 DevOps MCP Server 权限管理器。

    负责 Tool 调用前的权限校验，确保 AI Agent 只能在授权范围内操作。
    支持只读/执行两级权限：
    - 只读 Tool：默认开放（如 get_server_health、docker_list、docker_logs）
    - 执行 Tool：需要管理员在配置中显式开启 execute_tools_enabled

    新增：
    - 操作类型分类（READ / EXECUTE）
    - 结构化的权限校验结果
    - 安全上下文追踪
    """

    def __init__(self) -> None:
        self._allowed_tools: set[str] = set(settings.get_allowed_tools_list())
        self._blocked_commands: set[str] = set(settings.get_blocked_commands_list())

    @property
    def enabled(self) -> bool:
        """安全模式是否启用（实时读取 settings）。"""
        return settings.enable_security

    def classify_operation(self, tool_name: str) -> OperationType:
        """根据工具名称分类操作类型。

        读取配置中的 execute_tools 和 read_only_tools 列表来判断。

        Args:
            tool_name: 工具名称

        Returns:
            READ 或 EXECUTE
        """
        execute_tools = set(settings.get_execute_tools_list())
        if tool_name in execute_tools:
            return OperationType.EXECUTE
        return OperationType.READ

    def check_permission(self, tool_name: str) -> bool:
        """检查指定 Tool 是否允许调用。

        Args:
            tool_name: 工具名称

        Returns:
            True 表示允许调用，False 表示拒绝
        """
        if not self.enabled:
            return True

        if tool_name not in self._allowed_tools:
            logger.warning("权限拒绝: Tool '%s' 不在白名单中", tool_name)
            return False

        return True

    def check_permission_detailed(
        self,
        tool_name: str,
        context: dict[str, str] | None = None,
    ) -> PermissionResult:
        """详细的权限校验，返回结构化结果。

        同时检查基础权限和执行权限，返回完整的结果信息。

        Args:
            tool_name: 工具名称
            context: 安全上下文（可选，包含 caller、request_id 等）

        Returns:
            PermissionResult 结构体
        """
        operation_type = self.classify_operation(tool_name)
        module_name = self._get_module_name(tool_name)
        ctx = context or {}

        if not self.enabled:
            return PermissionResult(
                allowed=True,
                operation_type=operation_type,
                module_name=module_name,
                tool_name=tool_name,
                security_context=ctx,
            )

        # 检查模块白名单
        if module_name not in self._allowed_tools:
            return PermissionResult(
                allowed=False,
                operation_type=operation_type,
                reason=f"Tool '{tool_name}' 的模块 '{module_name}' 不在白名单中",
                module_name=module_name,
                tool_name=tool_name,
                security_context=ctx,
            )

        # 如果操作类型为 EXECUTE，进一步检查执行权限
        if operation_type == OperationType.EXECUTE:
            execute_enabled = settings.execute_tools_enabled
            execute_tools = set(settings.get_execute_tools_list())

            if not execute_enabled:
                return PermissionResult(
                    allowed=False,
                    operation_type=operation_type,
                    reason=(
                        f"Tool '{tool_name}' 需要执行权限，"
                        "但 execute_tools_enabled=False"
                    ),
                    module_name=module_name,
                    tool_name=tool_name,
                    security_context=ctx,
                )

            if tool_name not in execute_tools:
                return PermissionResult(
                    allowed=False,
                    operation_type=operation_type,
                    reason=f"Tool '{tool_name}' 不在执行工具列表中",
                    module_name=module_name,
                    tool_name=tool_name,
                    security_context=ctx,
                )

        return PermissionResult(
            allowed=True,
            operation_type=operation_type,
            module_name=module_name,
            tool_name=tool_name,
            security_context=ctx,
        )

    def _get_module_name(self, tool_name: str) -> str:
        """从工具名称中提取所属模块名。

        约定：工具名以模块名作为前缀，如 docker_restart -> docker

        Args:
            tool_name: 工具名称

        Returns:
            模块名称
        """
        return tool_name.split("_")[0] if "_" in tool_name else tool_name

    def check_execute_permission(self, tool_name: str) -> bool:
        """检查执行类 Tool 是否允许调用。

        执行类操作需要满足三个条件：
        1. 工具所属模块在模块白名单中（如 docker_restart -> docker）
        2. execute_tools_enabled = True（实时读取 settings）
        3. 工具在执行工具列表中

        Args:
            tool_name: 工具名称

        Returns:
            True 表示允许执行，False 表示拒绝
        """
        if not self.enabled:
            return True

        # 检查所属模块是否在白名单中
        module_name = self._get_module_name(tool_name)
        if module_name not in self._allowed_tools:
            logger.warning(
                "权限拒绝: Tool '%s' 的模块 '%s' 不在白名单中",
                tool_name, module_name,
            )
            return False

        # 实时读取 settings（支持测试中动态修改配置）
        execute_enabled = settings.execute_tools_enabled
        execute_tools = set(settings.get_execute_tools_list())

        if not execute_enabled:
            logger.warning(
                "执行权限拒绝: Tool '%s' 需要执行权限，但 execute_tools_enabled=False",
                tool_name,
            )
            return False

        if tool_name not in execute_tools:
            logger.warning(
                "执行权限拒绝: Tool '%s' 不在执行工具列表中", tool_name
            )
            return False

        return True

    def check_command(self, command: str) -> bool:
        """检查命令是否包含危险操作。

        Args:
            command: 待执行的命令

        Returns:
            True 表示安全，False 表示命令被拦截
        """
        command_lower = command.lower()
        for blocked in self._blocked_commands:
            if blocked.lower() in command_lower:
                logger.warning("危险命令拦截: '%s' 匹配黑名单 '%s'", command, blocked)
                return False
        return True

    def get_allowed_tools(self) -> set[str]:
        """获取当前允许的 Tool 列表。"""
        return self._allowed_tools.copy()

    def get_blocked_commands(self) -> set[str]:
        """获取当前拦截的命令列表。"""
        return self._blocked_commands.copy()

    def get_read_only_tools(self) -> set[str]:
        """获取当前只读工具列表（实时从 settings 读取）。"""
        return set(settings.get_read_only_tools_list())

    def get_execute_tools(self) -> set[str]:
        """获取当前执行工具列表（实时从 settings 读取）。"""
        return set(settings.get_execute_tools_list())

    @property
    def execute_enabled(self) -> bool:
        """执行操作全局开关是否开启（实时从 settings 读取）。"""
        return settings.execute_tools_enabled


# 全局权限管理器实例
_permission_manager = PermissionManager()


def get_permission_manager() -> PermissionManager:
    """获取全局权限管理器实例。"""
    return _permission_manager


def require_permission(tool_name: str) -> Callable[..., Any]:
    """基础权限校验装饰器（只读操作使用）。

    用于 Tool 函数的权限控制。在安全模式下，只有白名单中的 Tool 才会被调用。
    自动记录审计日志。

    Args:
        tool_name: 工具名称（用于白名单匹配）

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from app.security.audit import get_audit_logger

            import time

            start_time = time.time()
            caller = kwargs.pop("_caller", "unknown")
            request_id = kwargs.pop("_request_id", "")

            result = _permission_manager.check_permission_detailed(
                tool_name,
                context={"caller": caller, "request_id": request_id},
            )

            if result.allowed:
                try:
                    ret = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    get_audit_logger().log_call(
                        tool_name=tool_name,
                        arguments=_serialize_args(kwargs),
                        caller=caller,
                        permission_result="allowed",
                        execution_status="success",
                        execution_result=_serialize_result(ret),
                        duration_ms=duration,
                        request_id=request_id,
                    )
                    return ret
                except Exception as e:
                    duration = (time.time() - start_time) * 1000
                    get_audit_logger().log_call(
                        tool_name=tool_name,
                        arguments=_serialize_args(kwargs),
                        caller=caller,
                        permission_result="allowed",
                        execution_status="error",
                        execution_result=str(e),
                        duration_ms=duration,
                        request_id=request_id,
                    )
                    raise

            duration = (time.time() - start_time) * 1000
            get_audit_logger().log_call(
                tool_name=tool_name,
                arguments=_serialize_args(kwargs),
                caller=caller,
                permission_result="denied",
                execution_status="permission_denied",
                execution_result=result.reason,
                duration_ms=duration,
                request_id=request_id,
            )

            return {
                "error": "permission_denied",
                "message": result.reason or f"Tool '{tool_name}' 未被授权调用",
                "operation_type": result.operation_type.value if result.operation_type else "unknown",
                "module": result.module_name,
            }

        return wrapper

    return decorator


def require_execute_permission(tool_name: str) -> Callable[..., Any]:
    """执行权限校验装饰器（写操作使用）。

    比 require_permission 更严格的检查：
    1. 基础白名单检查
    2. execute_tools_enabled 必须为 True
    3. Tool 必须在执行工具列表中
    4. 额外执行安全保护（ExecuteProtector）

    自动记录审计日志。

    Args:
        tool_name: 工具名称（用于执行权限匹配）

    Returns:
        装饰器函数
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            from app.security.audit import get_audit_logger
            from app.security.execute_protection import get_execute_protector

            import time

            start_time = time.time()
            caller = kwargs.pop("_caller", "unknown")
            request_id = kwargs.pop("_request_id", "")

            # 1. 权限校验
            result = _permission_manager.check_permission_detailed(
                tool_name,
                context={"caller": caller, "request_id": request_id},
            )

            if not result.allowed:
                duration = (time.time() - start_time) * 1000
                get_audit_logger().log_call(
                    tool_name=tool_name,
                    arguments=_serialize_args(kwargs),
                    caller=caller,
                    permission_result="execute_denied",
                    execution_status="permission_denied",
                    execution_result=result.reason,
                    duration_ms=duration,
                    request_id=request_id,
                )
                return {
                    "error": "execute_permission_denied",
                    "message": (
                        f"Tool '{tool_name}' 需要执行权限，"
                        "请管理员设置 EXECUTE_TOOLS_ENABLED=true"
                    ),
                    "operation_type": "execute",
                    "module": result.module_name,
                }

            # 2. 执行安全保护——确认检查
            protector = get_execute_protector()
            if not protector.require_confirmation(tool_name):
                duration = (time.time() - start_time) * 1000
                get_audit_logger().log_call(
                    tool_name=tool_name,
                    arguments=_serialize_args(kwargs),
                    caller=caller,
                    permission_result="allowed",
                    execution_status="permission_denied",
                    execution_result="STRICT 模式下需要显式确认高危操作",
                    duration_ms=duration,
                    request_id=request_id,
                )
                return {
                    "error": "execute_not_confirmed",
                    "message": (
                        f"Tool '{tool_name}' 在 STRICT 保护模式下需要显式确认。"
                        "请先调用确认接口。"
                    ),
                    "operation_type": "execute",
                    "protection_level": "strict",
                }

            # 3. 执行安全保护——速率限制
            if not protector.check_rate_limit(tool_name):
                duration = (time.time() - start_time) * 1000
                get_audit_logger().log_call(
                    tool_name=tool_name,
                    arguments=_serialize_args(kwargs),
                    caller=caller,
                    permission_result="allowed",
                    execution_status="permission_denied",
                    execution_result="超过速率限制",
                    duration_ms=duration,
                    request_id=request_id,
                )
                return {
                    "error": "rate_limit_exceeded",
                    "message": (
                        f"Tool '{tool_name}' 调用频率过高，"
                        f"超过每分钟 {protector.max_calls_per_minute} 次的上限。"
                    ),
                    "operation_type": "execute",
                    "protection_level": protector.level.value,
                }

            # 4. 执行
            try:
                ret = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                get_audit_logger().log_call(
                    tool_name=tool_name,
                    arguments=_serialize_args(kwargs),
                    caller=caller,
                    permission_result="allowed",
                    execution_status="success",
                    execution_result=_serialize_result(ret),
                    duration_ms=duration,
                    request_id=request_id,
                )
                return ret
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                get_audit_logger().log_call(
                    tool_name=tool_name,
                    arguments=_serialize_args(kwargs),
                    caller=caller,
                    permission_result="allowed",
                    execution_status="error",
                    execution_result=str(e),
                    duration_ms=duration,
                    request_id=request_id,
                )
                raise

        return wrapper

    return decorator


def _serialize_args(kwargs: dict[str, Any]) -> dict[str, Any]:
    """序列化参数（过滤敏感字段、截断过长值）。"""
    sensitive_keys = {"api_key", "token", "password", "secret"}
    serialized: dict[str, Any] = {}
    for key, value in kwargs.items():
        if key.startswith("_") or key in sensitive_keys:
            serialized[key] = "***"
        elif isinstance(value, str) and len(value) > 200:
            serialized[key] = value[:200] + "..."
        else:
            serialized[key] = value
    return serialized


def _serialize_result(result: Any) -> str:
    """序列化执行结果（截断以避免日志过大）。"""
    import json

    try:
        text = json.dumps(result, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(result)
    if len(text) > 500:
        text = text[:500] + "..."
    return text