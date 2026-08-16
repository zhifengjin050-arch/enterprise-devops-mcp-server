"""审计日志模块（Audit Logger）。

记录所有 Tool 调用的完整审计信息，包括：
- 调用时间、工具名称、参数
- 权限校验结果
- 执行结果与耗时
- 安全上下文

所有日志保存在内存环形缓冲区中，不引入数据库依赖。
"""

import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AuditLogEntry:
    """单条审计日志条目。"""

    timestamp: str
    """ISO 格式时间戳"""

    tool_name: str
    """被调用的 Tool 名称"""

    arguments: dict[str, Any]
    """调用参数"""

    caller: str
    """调用方标识"""

    permission_result: str
    """权限校验结果: allowed / denied / execute_denied"""

    execution_status: str
    """执行状态: success / error / permission_denied / not_found"""

    execution_result: str
    """执行结果摘要（截断至 500 字符）"""

    duration_ms: float
    """执行耗时（毫秒）"""

    request_id: str
    """请求唯一标识"""

    def to_dict(self) -> dict[str, Any]:
        """转换为可序列化的字典。"""
        result = asdict(self)
        return result

    def to_json(self) -> str:
        """转换为 JSON 字符串。"""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)


class AuditLogger:
    """审计日志管理器。

    线程安全，使用环形缓冲区存储最近的日志条目。
    默认保留最近 1000 条记录，防止内存无限增长。
    """

    def __init__(self, max_entries: int = 1000) -> None:
        self._max_entries = max_entries
        self._logs: deque[AuditLogEntry] = deque(maxlen=max_entries)
        self._lock = threading.Lock()
        self._enabled: bool = True
        logger.info("AuditLogger 初始化完成，最大记录数: %d", max_entries)

    @property
    def enabled(self) -> bool:
        """审计日志是否启用。"""
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """启用或禁用审计日志。"""
        self._enabled = value
        logger.info("AuditLogger %s", "已启用" if value else "已禁用")

    def log_call(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        caller: str = "unknown",
        permission_result: str = "allowed",
        execution_status: str = "success",
        execution_result: str = "",
        duration_ms: float = 0.0,
        request_id: str = "",
    ) -> None:
        """记录一次 Tool 调用。

        Args:
            tool_name: Tool 名称
            arguments: 调用参数
            caller: 调用方标识
            permission_result: 权限校验结果
            execution_status: 执行状态
            execution_result: 执行结果摘要
            duration_ms: 耗时（毫秒）
            request_id: 请求 ID
        """
        if not self._enabled:
            return

        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool_name=tool_name,
            arguments=arguments or {},
            caller=caller,
            permission_result=permission_result,
            execution_status=execution_status,
            execution_result=execution_result[:500],
            duration_ms=round(duration_ms, 2),
            request_id=request_id or self._generate_request_id(),
        )

        with self._lock:
            self._logs.append(entry)

    def get_recent_logs(
        self,
        count: int = 50,
        tool_name: str | None = None,
        status: str | None = None,
    ) -> list[AuditLogEntry]:
        """获取最近的审计日志。

        Args:
            count: 返回条数
            tool_name: 按工具名称过滤（可选）
            status: 按执行状态过滤（可选）

        Returns:
            审计日志条目列表（按时间倒序）
        """
        with self._lock:
            logs = list(self._logs)

        # 倒序（最新的在前）
        logs.reverse()

        # 过滤
        if tool_name:
            logs = [e for e in logs if e.tool_name == tool_name]
        if status:
            logs = [e for e in logs if e.execution_status == status]

        return logs[:count]

    def get_stats(self) -> dict[str, Any]:
        """获取审计统计信息。

        Returns:
            包含总调用数、成功/失败统计等的字典
        """
        with self._lock:
            total = len(self._logs)
            if total == 0:
                return {
                    "total_calls": 0,
                    "success": 0,
                    "error": 0,
                    "permission_denied": 0,
                    "avg_duration_ms": 0.0,
                    "tools_used": [],
                }

            success = sum(1 for e in self._logs if e.execution_status == "success")
            error = sum(1 for e in self._logs if e.execution_status == "error")
            denied = sum(
                1
                for e in self._logs
                if e.execution_status == "permission_denied"
            )
            avg_duration = sum(e.duration_ms for e in self._logs) / total
            tools_used = list({e.tool_name for e in self._logs})

            return {
                "total_calls": total,
                "success": success,
                "error": error,
                "permission_denied": denied,
                "avg_duration_ms": round(avg_duration, 2),
                "tools_used": sorted(tools_used),
            }

    def clear(self) -> None:
        """清空所有审计日志。"""
        with self._lock:
            self._logs.clear()
        logger.info("审计日志已清空")

    def get_all_logs(self) -> list[AuditLogEntry]:
        """获取所有审计日志（按时间正序）。

        Returns:
            所有审计日志条目
        """
        with self._lock:
            return list(self._logs)

    @staticmethod
    def _generate_request_id() -> str:
        """生成简单的请求 ID。"""
        import uuid

        return uuid.uuid4().hex[:12]


# 全局审计日志实例
_audit_logger = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """获取全局审计日志实例。"""
    return _audit_logger