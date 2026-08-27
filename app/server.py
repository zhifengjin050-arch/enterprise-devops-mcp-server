"""Enterprise DevOps MCP Server 入口模块。

基于 FastMCP 框架实现的 MCP Server，注册所有 DevOps Tool 并提供启动入口。
集成安全体系：Permission Control、Audit Logging、Execute Protection。
"""

import logging
import sys

from fastmcp import FastMCP

from app.config import settings
from app.tools import register_all_tools

# ---- 日志（全部输出到 stderr，stdout 只用于 MCP 协议） ----
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
# 抑制 FastMCP 内部日志
logging.getLogger("fastmcp").setLevel(logging.WARNING)
logging.getLogger("mcp").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ---- FastMCP 实例 ----
mcp = FastMCP(
    name=settings.mcp_server_name,
    version=settings.mcp_server_version,
)


def init_security() -> None:
    """初始化安全体系。

    从配置读取参数并注入到全局安全组件：
    - AuditLogger：审计日志
    - ExecuteProtector：执行安全保护
    """
    from app.security.audit import get_audit_logger

    audit_logger = get_audit_logger()
    audit_logger.enabled = settings.audit_log_enabled

    from app.security.execute_protection import get_execute_protector, ProtectionLevel

    protector = get_execute_protector()
    protector.level = ProtectionLevel(settings.execute_protection_level)
    protector.max_calls_per_minute = settings.execute_max_calls_per_minute

    logger.info("安全体系初始化完成")
    logger.info("  Kubernetes 模块: %s", "已启用" if settings.k8s_enabled else "已禁用")
    logger.info("  Audit Logger: %s", "已启用" if audit_logger.enabled else "已禁用")
    logger.info("  执行保护等级: %s", protector.level.value)
    logger.info("  速率限制: %d 次/分钟", protector.max_calls_per_minute)
    logger.info("  安全模式: %s", "已启用" if settings.enable_security else "已禁用")
    logger.info("  传输: stdio（信任能拉起本进程的调用方；API_KEY 预留给 HTTP 封装）")


def init_server() -> FastMCP:
    """初始化 MCP Server，注册所有 Tool。

    Returns:
        已配置完成的 FastMCP 实例
    """
    logger.info(
        "正在初始化 %s v%s ...",
        settings.mcp_server_name,
        settings.mcp_server_version,
    )

    # 初始化安全体系
    init_security()

    # 注册所有 DevOps Tool
    register_all_tools(mcp)

    logger.info("Tool 注册完毕，共注册 %d 个模块", 4)

    return mcp


def main() -> None:
    """Server 启动入口。"""
    init_server()
    logger.info("%s 启动中 ...", settings.mcp_server_name)
    # stdio 模式下必须关闭横幅：横幅会污染 stdout，导致 Cursor MCP 握手失败
    mcp.run(show_banner=False)


if __name__ == "__main__":
    main()