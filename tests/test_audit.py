"""Audit Logger 模块测试。"""

import json
import threading
import time

import pytest

from app.security.audit import AuditLogger, AuditLogEntry, get_audit_logger


class TestAuditLogEntry:
    """AuditLogEntry 数据类测试。"""

    def test_to_dict_contains_all_fields(self) -> None:
        """验证 to_dict 返回所有字段。"""
        entry = AuditLogEntry(
            timestamp="2024-01-01T00:00:00",
            tool_name="test_tool",
            arguments={"key": "value"},
            caller="test_caller",
            permission_result="allowed",
            execution_status="success",
            execution_result="ok",
            duration_ms=10.5,
            request_id="req123",
        )
        data = entry.to_dict()
        expected_keys = {
            "timestamp", "tool_name", "arguments", "caller",
            "permission_result", "execution_status", "execution_result",
            "duration_ms", "request_id",
        }
        assert set(data.keys()) == expected_keys

    def test_to_json_valid(self) -> None:
        """验证 to_json 输出合法 JSON。"""
        entry = AuditLogEntry(
            timestamp="2024-01-01T00:00:00",
            tool_name="test_tool",
            arguments={},
            caller="caller",
            permission_result="allowed",
            execution_status="success",
            execution_result="ok",
            duration_ms=0.0,
            request_id="rid",
        )
        parsed = json.loads(entry.to_json())
        assert parsed["tool_name"] == "test_tool"
        assert parsed["execution_status"] == "success"


class TestAuditLogger:
    """AuditLogger 管理器测试。"""

    def setup_method(self) -> None:
        """每个测试前创建新实例。"""
        self.logger = AuditLogger(max_entries=100)

    def test_initial_state(self) -> None:
        """验证初始状态。"""
        assert self.logger.enabled is True
        stats = self.logger.get_stats()
        assert stats["total_calls"] == 0

    def test_log_call_adds_entry(self) -> None:
        """验证 log_call 添加条目。"""
        self.logger.log_call(
            tool_name="get_server_health",
            arguments={},
            caller="cursor",
            permission_result="allowed",
            execution_status="success",
        )
        stats = self.logger.get_stats()
        assert stats["total_calls"] == 1
        assert stats["success"] == 1

    def test_log_call_disabled(self) -> None:
        """验证禁用时不记录日志。"""
        self.logger.enabled = False
        self.logger.log_call(tool_name="test", arguments={})
        stats = self.logger.get_stats()
        assert stats["total_calls"] == 0

    def test_multiple_calls_tracked(self) -> None:
        """验证多次调用正确统计。"""
        for i in range(5):
            self.logger.log_call(
                tool_name=f"tool_{i}",
                arguments={"index": i},
                execution_status="success" if i % 2 == 0 else "error",
            )
        stats = self.logger.get_stats()
        assert stats["total_calls"] == 5
        assert stats["success"] == 3
        assert stats["error"] == 2
        assert len(stats["tools_used"]) == 5

    def test_get_recent_logs_returns_latest(self) -> None:
        """验证 get_recent_logs 返回最新条目。"""
        for i in range(10):
            self.logger.log_call(
                tool_name=f"tool_{i}",
                execution_status="success",
            )
        recent = self.logger.get_recent_logs(count=3)
        assert len(recent) == 3
        # 最新的先返回
        assert recent[0].tool_name == "tool_9"

    def test_get_recent_logs_filter_by_tool(self) -> None:
        """验证按工具名称过滤。"""
        self.logger.log_call(tool_name="docker_list")
        self.logger.log_call(tool_name="docker_logs")
        self.logger.log_call(tool_name="docker_list")
        filtered = self.logger.get_recent_logs(tool_name="docker_list", count=10)
        assert len(filtered) == 2
        assert all(e.tool_name == "docker_list" for e in filtered)

    def test_get_recent_logs_filter_by_status(self) -> None:
        """验证按状态过滤。"""
        self.logger.log_call(tool_name="t1", execution_status="success")
        self.logger.log_call(tool_name="t2", execution_status="error")
        self.logger.log_call(tool_name="t3", execution_status="success")
        filtered = self.logger.get_recent_logs(status="error", count=10)
        assert len(filtered) == 1
        assert filtered[0].execution_status == "error"

    def test_get_stats_empty(self) -> None:
        """验证空日志的统计。"""
        empty_logger = AuditLogger(max_entries=10)
        stats = empty_logger.get_stats()
        assert stats["total_calls"] == 0
        assert stats["avg_duration_ms"] == 0.0

    def test_get_stats_avg_duration(self) -> None:
        """验证平均耗时统计。"""
        for _ in range(4):
            self.logger.log_call(
                tool_name="tool",
                duration_ms=10.0,
            )
        stats = self.logger.get_stats()
        assert stats["avg_duration_ms"] == 10.0

    def test_clear_removes_all_logs(self) -> None:
        """验证清空操作。"""
        self.logger.log_call(tool_name="t1")
        self.logger.log_call(tool_name="t2")
        assert self.logger.get_stats()["total_calls"] == 2
        self.logger.clear()
        assert self.logger.get_stats()["total_calls"] == 0

    def test_max_entries_respected(self) -> None:
        """验证环形缓冲区上限。"""
        limited_logger = AuditLogger(max_entries=5)
        for i in range(20):
            limited_logger.log_call(
                tool_name=f"tool_{i}",
                arguments={"i": i},
            )
        stats = limited_logger.get_stats()
        assert stats["total_calls"] == 5
        # 最新的 5 条
        tools = stats["tools_used"]
        assert "tool_19" in tools
        assert "tool_15" in tools

    def test_get_all_logs_ordered(self) -> None:
        """验证 get_all_logs 返回正序。"""
        self.logger.log_call(tool_name="first")
        self.logger.log_call(tool_name="second")
        all_logs = self.logger.get_all_logs()
        assert len(all_logs) == 2
        assert all_logs[0].tool_name == "first"
        assert all_logs[1].tool_name == "second"

    def test_enabled_setter(self) -> None:
        """验证 enabled setter。"""
        assert self.logger.enabled is True
        self.logger.enabled = False
        assert self.logger.enabled is False
        self.logger.enabled = True
        assert self.logger.enabled is True

    def test_execution_result_truncated(self) -> None:
        """验证执行结果截断。"""
        long_result = "x" * 1000
        self.logger.log_call(
            tool_name="tool",
            execution_result=long_result,
        )
        logs = self.logger.get_all_logs()
        assert len(logs[0].execution_result) == 500

    def test_permission_denied_stats(self) -> None:
        """验证权限拒绝统计。"""
        self.logger.log_call(
            tool_name="t1",
            execution_status="permission_denied",
        )
        self.logger.log_call(
            tool_name="t2",
            execution_status="success",
        )
        stats = self.logger.get_stats()
        assert stats["permission_denied"] == 1

    def test_thread_safety(self) -> None:
        """验证线程安全。"""
        errors: list[Exception] = []
        # 使用更大的缓冲区以容纳所有线程调用
        big_logger = AuditLogger(max_entries=500)

        def log_thread(thread_id: int) -> None:
            try:
                for i in range(50):
                    big_logger.log_call(
                        tool_name=f"thread_{thread_id}_call_{i}",
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=log_thread, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        stats = big_logger.get_stats()
        assert stats["total_calls"] == 250


class TestAuditLoggerGlobal:
    """全局 AuditLogger 实例测试。"""

    def test_get_audit_logger_returns_singleton(self) -> None:
        """验证 get_audit_logger 返回单例。"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        assert logger1 is logger2