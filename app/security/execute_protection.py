"""执行安全保护模块（Execute Protection）。

提供执行类操作的额外安全保护层，包括：
- 保护等级控制（off / basic / strict）
- 速率限制（限制每分钟最大执行次数）
- 高危操作确认机制（strict 模式下需显式确认）

与 PermissionManager 协同工作，在权限校验之后提供第二层保护。
不引入数据库，所有状态保存在内存中。
"""

import enum
import logging
import threading
import time
from collections import deque
from typing import Any

logger = logging.getLogger(__name__)


class ProtectionLevel(str, enum.Enum):
    """执行保护等级。"""

    OFF = "off"
    """关闭保护——不进行额外检查（仅依赖 PermissionManager）"""

    BASIC = "basic"
    """基础保护——启用速率限制，每分钟最多执行 N 次"""

    STRICT = "strict"
    """严格保护——启用速率限制 + 高危操作确认机制"""


class ExecuteProtector:
    """执行操作保护器。

    线程安全，在权限校验通过后提供额外的执行安全保护层。

    Attributes:
        level: 当前保护等级
        max_calls_per_minute: 每分钟最大执行次数
    """

    def __init__(
        self,
        level: str = "basic",
        max_calls_per_minute: int = 10,
    ) -> None:
        self._level = ProtectionLevel(level)
        self._max_calls_per_minute = max_calls_per_minute
        self._call_timestamps: deque[float] = deque(maxlen=200)
        self._lock = threading.Lock()
        self._confirmed_actions: set[str] = set()
        logger.info(
            "ExecuteProtector 初始化完成，等级: %s，速率限制: %d 次/分钟",
            level,
            max_calls_per_minute,
        )

    @property
    def level(self) -> ProtectionLevel:
        """当前保护等级。"""
        return self._level

    @level.setter
    def level(self, value: ProtectionLevel) -> None:
        """设置保护等级。"""
        self._level = value
        logger.info("执行保护等级已设置为: %s", value.value)

    @property
    def max_calls_per_minute(self) -> int:
        """每分钟最大执行次数。"""
        return self._max_calls_per_minute

    @max_calls_per_minute.setter
    def max_calls_per_minute(self, value: int) -> None:
        """设置每分钟最大执行次数。"""
        self._max_calls_per_minute = value
        logger.info("执行速率限制已设置为: %d 次/分钟", value)

    def check_rate_limit(self, tool_name: str) -> bool:
        """检查是否超过速率限制。

        统计最近 60 秒内的执行调用次数，如果超过上限则拒绝。

        Args:
            tool_name: 工具名称（仅用于日志记录）

        Returns:
            True 表示未超限，可以执行；False 表示已超限
        """
        if self._level == ProtectionLevel.OFF:
            return True

        now = time.time()
        cutoff = now - 60.0

        with self._lock:
            # 清理过期记录
            while self._call_timestamps and self._call_timestamps[0] < cutoff:
                self._call_timestamps.popleft()

            current_count = len(self._call_timestamps)

            if current_count >= self._max_calls_per_minute:
                logger.warning(
                    "速率限制触发: Tool '%s' 在 60 秒内已调用 %d 次（上限 %d）",
                    tool_name,
                    current_count,
                    self._max_calls_per_minute,
                )
                return False

            # 记录本次调用时间戳
            self._call_timestamps.append(now)

        return True

    def require_confirmation(self, tool_name: str) -> bool:
        """检查高危操作是否需要确认。

        在 strict 模式下，执行操作需要先通过 confirm_action 确认。

        Args:
            tool_name: 工具名称

        Returns:
            True 表示已确认或无需确认，False 表示需要确认
        """
        if self._level != ProtectionLevel.STRICT:
            return True

        with self._lock:
            if tool_name in self._confirmed_actions:
                return True

        logger.warning(
            "高危操作确认触发: Tool '%s' 需要显式确认后才能执行（STRICT 模式）",
            tool_name,
        )
        return False

    def confirm_action(self, tool_name: str) -> None:
        """确认一个高危操作。

        在 strict 模式下，调用此方法标记某个 Tool 为已确认状态，
        后续调用 require_confirmation 将返回 True。

        Args:
            tool_name: 工具名称
        """
        with self._lock:
            self._confirmed_actions.add(tool_name)
        logger.info("高危操作已确认: '%s'", tool_name)

    def reset_confirmation(self, tool_name: str | None = None) -> None:
        """重置确认状态。

        Args:
            tool_name: 指定工具名称（None 时重置所有）
        """
        with self._lock:
            if tool_name:
                self._confirmed_actions.discard(tool_name)
                logger.info("高危操作确认已重置: '%s'", tool_name)
            else:
                self._confirmed_actions.clear()
                logger.info("所有高危操作确认已重置")

    def get_status(self) -> dict[str, Any]:
        """获取当前保护状态。"""
        with self._lock:
            now = time.time()
            cutoff = now - 60.0
            recent_count = sum(1 for t in self._call_timestamps if t >= cutoff)
            confirmed_count = len(self._confirmed_actions)

        return {
            "level": self._level.value,
            "max_calls_per_minute": self._max_calls_per_minute,
            "recent_calls_60s": recent_count,
            "confirmed_actions": sorted(self._confirmed_actions),
            "confirmed_count": confirmed_count,
        }


# 全局执行保护器实例
_execute_protector = ExecuteProtector()


def get_execute_protector() -> ExecuteProtector:
    """获取全局执行保护器实例。"""
    return _execute_protector