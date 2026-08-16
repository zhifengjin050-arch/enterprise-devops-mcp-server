"""Execute Protection 模块测试。"""

import threading
import time

import pytest

from app.security.execute_protection import (
    ExecuteProtector,
    ProtectionLevel,
    get_execute_protector,
)


class TestProtectionLevel:
    """ProtectionLevel 枚举测试。"""

    def test_enum_values(self) -> None:
        """验证枚举值。"""
        assert ProtectionLevel.OFF.value == "off"
        assert ProtectionLevel.BASIC.value == "basic"
        assert ProtectionLevel.STRICT.value == "strict"

    def test_enum_from_string(self) -> None:
        """验证字符串转枚举。"""
        assert ProtectionLevel("off") == ProtectionLevel.OFF
        assert ProtectionLevel("basic") == ProtectionLevel.BASIC
        assert ProtectionLevel("strict") == ProtectionLevel.STRICT


class TestExecuteProtectorInit:
    """ExecuteProtector 初始化测试。"""

    def test_default_level_is_basic(self) -> None:
        """验证默认保护等级为 basic。"""
        protector = ExecuteProtector()
        assert protector.level == ProtectionLevel.BASIC

    def test_custom_level(self) -> None:
        """验证自定义保护等级。"""
        protector = ExecuteProtector(level="strict")
        assert protector.level == ProtectionLevel.STRICT

    def test_custom_max_calls(self) -> None:
        """验证自定义速率限制。"""
        protector = ExecuteProtector(max_calls_per_minute=5)
        assert protector.max_calls_per_minute == 5

    def test_level_setter(self) -> None:
        """验证 level setter。"""
        protector = ExecuteProtector()
        protector.level = ProtectionLevel.OFF
        assert protector.level == ProtectionLevel.OFF

    def test_max_calls_setter(self) -> None:
        """验证 max_calls_per_minute setter。"""
        protector = ExecuteProtector()
        protector.max_calls_per_minute = 20
        assert protector.max_calls_per_minute == 20


class TestRateLimit:
    """速率限制测试。"""

    def test_rate_limit_off_disabled(self) -> None:
        """验证 OFF 等级不检查速率。"""
        protector = ExecuteProtector(level="off", max_calls_per_minute=3)
        for _ in range(10):
            assert protector.check_rate_limit("tool") is True

    def test_rate_limit_basic_allows_within_limit(self) -> None:
        """验证 BASIC 等级在限制内允许。"""
        protector = ExecuteProtector(level="basic", max_calls_per_minute=10)
        for _ in range(10):
            assert protector.check_rate_limit("tool") is True

    def test_rate_limit_basic_blocks_exceeding(self) -> None:
        """验证 BASIC 等级超限时阻止。"""
        protector = ExecuteProtector(level="basic", max_calls_per_minute=5)
        for _ in range(5):
            assert protector.check_rate_limit("tool") is True
        # 第 6 次应被阻止
        assert protector.check_rate_limit("tool") is False

    def test_rate_limit_window_sliding(self) -> None:
        """验证速率窗口滑动后允许新调用。"""
        protector = ExecuteProtector(level="basic", max_calls_per_minute=2)
        assert protector.check_rate_limit("tool") is True
        assert protector.check_rate_limit("tool") is True
        assert protector.check_rate_limit("tool") is False

    def test_rate_limit_strict_same_as_basic(self) -> None:
        """验证 STRICT 等级速率限制与 BASIC 相同。"""
        protector = ExecuteProtector(level="strict", max_calls_per_minute=3)
        for _ in range(3):
            assert protector.check_rate_limit("tool") is True
        assert protector.check_rate_limit("tool") is False


class TestConfirmation:
    """高危操作确认测试。"""

    def test_strict_requires_confirmation(self) -> None:
        """验证 STRICT 模式下需要确认。"""
        protector = ExecuteProtector(level="strict")
        assert protector.require_confirmation("docker_restart") is False

    def test_strict_after_confirmation_allows(self) -> None:
        """验证确认后允许执行。"""
        protector = ExecuteProtector(level="strict")
        protector.confirm_action("docker_restart")
        assert protector.require_confirmation("docker_restart") is True

    def test_strict_unconfirmed_tool_still_blocked(self) -> None:
        """验证未确认的 Tool 仍被阻止。"""
        protector = ExecuteProtector(level="strict")
        protector.confirm_action("docker_restart")
        assert protector.require_confirmation("docker_logs") is False

    def test_basic_no_confirmation_needed(self) -> None:
        """验证 BASIC 模式不需要确认。"""
        protector = ExecuteProtector(level="basic")
        assert protector.require_confirmation("docker_restart") is True

    def test_off_no_confirmation_needed(self) -> None:
        """验证 OFF 模式不需要确认。"""
        protector = ExecuteProtector(level="off")
        assert protector.require_confirmation("docker_restart") is True

    def test_reset_confirmation_single_tool(self) -> None:
        """验证重置单个工具确认。"""
        protector = ExecuteProtector(level="strict")
        protector.confirm_action("docker_restart")
        assert protector.require_confirmation("docker_restart") is True
        protector.reset_confirmation("docker_restart")
        assert protector.require_confirmation("docker_restart") is False

    def test_reset_all_confirmations(self) -> None:
        """验证重置所有确认。"""
        protector = ExecuteProtector(level="strict")
        protector.confirm_action("t1")
        protector.confirm_action("t2")
        protector.reset_confirmation()
        assert protector.require_confirmation("t1") is False
        assert protector.require_confirmation("t2") is False


class TestGetStatus:
    """get_status 方法测试。"""

    def test_status_contains_all_fields(self) -> None:
        """验证状态包含所有字段。"""
        protector = ExecuteProtector(level="basic", max_calls_per_minute=10)
        status = protector.get_status()
        expected_keys = {
            "level", "max_calls_per_minute",
            "recent_calls_60s", "confirmed_actions", "confirmed_count",
        }
        assert set(status.keys()) == expected_keys

    def test_status_reflects_config(self) -> None:
        """验证状态反映当前配置。"""
        protector = ExecuteProtector(level="strict", max_calls_per_minute=5)
        status = protector.get_status()
        assert status["level"] == "strict"
        assert status["max_calls_per_minute"] == 5
        assert status["confirmed_count"] == 0

    def test_status_with_confirmations(self) -> None:
        """验证状态包含已确认操作。"""
        protector = ExecuteProtector(level="strict")
        protector.confirm_action("t1")
        protector.confirm_action("t2")
        status = protector.get_status()
        assert status["confirmed_count"] == 2
        assert "t1" in status["confirmed_actions"]
        assert "t2" in status["confirmed_actions"]

    def test_status_recent_calls(self) -> None:
        """验证状态包含近期调用计数。"""
        protector = ExecuteProtector(level="basic", max_calls_per_minute=20)
        for _ in range(5):
            assert protector.check_rate_limit("tool") is True
        status = protector.get_status()
        assert status["recent_calls_60s"] == 5


class TestThreadSafety:
    """线程安全测试。"""

    def test_thread_safe_rate_limit(self) -> None:
        """验证速率限制线程安全。"""
        protector = ExecuteProtector(level="basic", max_calls_per_minute=100)
        errors: list[Exception] = []

        def call_thread() -> None:
            try:
                for _ in range(10):
                    protector.check_rate_limit("tool")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=call_thread) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0

    def test_thread_safe_confirmation(self) -> None:
        """验证确认操作线程安全。"""
        protector = ExecuteProtector(level="strict")
        errors: list[Exception] = []

        def confirm_thread() -> None:
            try:
                for i in range(10):
                    protector.confirm_action(f"tool_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=confirm_thread) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # 最终工具数量应为 10（各线程操作不同工具）
        assert protector.get_status()["confirmed_count"] == 10


class TestGlobalProtector:
    """全局 ExecuteProtector 实例测试。"""

    def test_get_execute_protector_returns_singleton(self) -> None:
        """验证 get_execute_protector 返回单例。"""
        p1 = get_execute_protector()
        p2 = get_execute_protector()
        assert p1 is p2