"""Kubernetes 工具模块。

提供 K8s 集群管理运维能力，包括：
- Pod 状态查询（k8s_get_pods）
- Deployment 状态查询（k8s_get_deployments）
- Service 信息查询（k8s_get_services）
- Pod 日志查询（k8s_logs）

基于 kubernetes Python client 实现。
"""

import logging
from typing import Annotated, Any

from fastmcp import FastMCP

from app.config import settings
from app.security.permission import require_permission

logger = logging.getLogger(__name__)


def _get_k8s_client() -> tuple[Any, Any, Any]:
    """初始化 Kubernetes 客户端。

    加载 kubeconfig 并返回 CoreV1Api 和 AppsV1Api 实例。

    Returns:
        (CoreV1Api, AppsV1Api, CoreV1Api) 分别用于 Pod/Service、Deployment 操作

    Raises:
        Exception: kubeconfig 加载失败或集群连接失败时抛出
    """
    import kubernetes
    from kubernetes import client, config

    # 加载 kubeconfig
    if settings.k8s_kubeconfig_path:
        config.load_kube_config(config_file=settings.k8s_kubeconfig_path)
    else:
        config.load_kube_config()

    core_api = client.CoreV1Api()
    apps_api = client.AppsV1Api()

    return core_api, apps_api, core_api


def _safe_get_namespace(namespace: str) -> str:
    """获取安全的命名空间值。

    Args:
        namespace: 用户传入的命名空间

    Returns:
        有效的命名空间字符串
    """
    return namespace or settings.k8s_namespace


@require_permission("kubernetes")
def k8s_get_pods(
    namespace: Annotated[str, "Kubernetes 命名空间，默认 default"] = "default",
) -> list[dict[str, str]]:
    """获取 Kubernetes 集群中指定命名空间的 Pod 状态列表。

    返回每个 Pod 的名称、命名空间、状态、就绪容器数/总容器数、
    重启次数和所在节点信息。

    用于 AI Agent 排查 Pod 运行状态、分析容器重启原因、查看调度情况。

    Args:
        namespace: 命名空间，默认 "default"

    Returns:
        Pod 信息列表，每个元素包含 name, namespace, status, ready, restarts, node

    异常时返回 [{"status": "error", "message": "..."}]
    """
    logger.info("Tool 调用: k8s_get_pods (namespace=%s)", namespace)
    ns = _safe_get_namespace(namespace)

    try:
        core_api, _, _ = _get_k8s_client()
        pods = core_api.list_namespaced_pod(namespace=ns)

        result: list[dict[str, str]] = []
        for pod in pods.items:
            pod_name = pod.metadata.name or ""
            pod_namespace = pod.metadata.namespace or ns
            pod_status = pod.status.phase if pod.status else "Unknown"

            # 计算 Ready 状态（ready / total）
            ready_count = 0
            total_count = 0
            if pod.status and pod.status.container_statuses:
                total_count = len(pod.status.container_statuses)
                ready_count = sum(
                    1 for c in pod.status.container_statuses if c.ready
                )

            # 计算重启次数
            restarts = 0
            if pod.status and pod.status.container_statuses:
                restarts = sum(
                    c.restart_count for c in pod.status.container_statuses
                )

            # 节点名称
            node_name = pod.spec.node_name if pod.spec else ""

            result.append({
                "name": pod_name,
                "namespace": pod_namespace,
                "status": pod_status,
                "ready": f"{ready_count}/{total_count}",
                "restarts": str(restarts),
                "node": node_name or "-",
            })

        return result

    except Exception as e:
        logger.error("K8s Pod 查询失败: %s", e)
        return _handle_k8s_error(e)


@require_permission("kubernetes")
def k8s_get_deployments(
    namespace: Annotated[str, "Kubernetes 命名空间，默认 default"] = "default",
) -> list[dict[str, str]]:
    """获取 Kubernetes 集群中指定命名空间的 Deployment 状态列表。

    返回每个 Deployment 的名称、命名空间、期望副本数、实际副本数和可用副本数。

    用于 AI Agent 检查服务部署状态、确认滚动更新是否完成、排查副本数异常。

    Args:
        namespace: 命名空间，默认 "default"

    Returns:
        Deployment 信息列表，每个元素包含 name, namespace, replicas, available

    异常时返回 [{"status": "error", "message": "..."}]
    """
    logger.info("Tool 调用: k8s_get_deployments (namespace=%s)", namespace)
    ns = _safe_get_namespace(namespace)

    try:
        _, apps_api, _ = _get_k8s_client()
        deployments = apps_api.list_namespaced_deployment(namespace=ns)

        result: list[dict[str, str]] = []
        for dep in deployments.items:
            dep_name = dep.metadata.name or ""
            dep_namespace = dep.metadata.namespace or ns

            replicas = 0
            available = 0
            if dep.spec and dep.spec.replicas is not None:
                replicas = dep.spec.replicas
            if dep.status and dep.status.available_replicas is not None:
                available = dep.status.available_replicas

            result.append({
                "name": dep_name,
                "namespace": dep_namespace,
                "replicas": str(replicas),
                "available": str(available),
            })

        return result

    except Exception as e:
        logger.error("K8s Deployment 查询失败: %s", e)
        return _handle_k8s_error(e)


@require_permission("kubernetes")
def k8s_get_services(
    namespace: Annotated[str, "Kubernetes 命名空间，默认 default"] = "default",
) -> list[dict[str, str]]:
    """获取 Kubernetes 集群中指定命名空间的 Service 信息列表。

    返回每个 Service 的名称、类型、Cluster IP 和端口信息。

    用于 AI Agent 查看服务暴露方式、确认网络连通性、排查服务发现问题。

    Args:
        namespace: 命名空间，默认 "default"

    Returns:
        Service 信息列表，每个元素包含 name, type, cluster_ip, ports

    异常时返回 [{"status": "error", "message": "..."}]
    """
    logger.info("Tool 调用: k8s_get_services (namespace=%s)", namespace)
    ns = _safe_get_namespace(namespace)

    try:
        core_api, _, _ = _get_k8s_client()
        services = core_api.list_namespaced_service(namespace=ns)

        result: list[dict[str, str]] = []
        for svc in services.items:
            svc_name = svc.metadata.name or ""
            svc_type = svc.spec.type if svc.spec else "ClusterIP"
            cluster_ip = svc.spec.cluster_ip if svc.spec else "-"

            # 解析端口
            ports_str = "-"
            if svc.spec and svc.spec.ports:
                port_parts: list[str] = []
                for port in svc.spec.ports:
                    p = port.port
                    if port.node_port:
                        port_parts.append(f"{p}:{port.node_port}/{port.protocol}")
                    else:
                        port_parts.append(f"{p}/{port.protocol}")
                ports_str = ", ".join(port_parts)

            result.append({
                "name": svc_name,
                "type": svc_type,
                "cluster_ip": cluster_ip,
                "ports": ports_str,
            })

        return result

    except Exception as e:
        logger.error("K8s Service 查询失败: %s", e)
        return _handle_k8s_error(e)


@require_permission("kubernetes")
def k8s_logs(
    pod_name: Annotated[str, "Pod 名称，必填"],
    namespace: Annotated[str, "Kubernetes 命名空间，默认 default"] = "default",
    lines: Annotated[int, "返回日志的行数，默认 100"] = 100,
) -> dict[str, str]:
    """获取指定 Kubernetes Pod 的容器日志。

    用于 AI Agent 排查 Pod 运行异常、分析应用错误日志。

    Args:
        pod_name: Pod 名称
        namespace: 命名空间，默认 "default"
        lines: 返回日志行数，默认 100

    Returns:
        包含 pod, namespace, logs 字段的字典

    异常时返回 {"status": "error", "message": "..."}
    """
    logger.info(
        "Tool 调用: k8s_logs (pod=%s, namespace=%s, lines=%d)",
        pod_name, namespace, lines,
    )
    ns = _safe_get_namespace(namespace)

    try:
        core_api, _, _ = _get_k8s_client()
        log_data = core_api.read_namespaced_pod_log(
            name=pod_name,
            namespace=ns,
            tail_lines=lines,
        )
        log_text = log_data if log_data else ""

        return {
            "pod": pod_name,
            "namespace": ns,
            "logs": log_text,
        }

    except Exception as e:
        logger.error("K8s 日志查询失败: %s", e)
        return _handle_k8s_single_error(e)


def _handle_k8s_error(error: Exception) -> list[dict[str, str]]:
    """统一处理 K8s 异常（列表返回）。

    Args:
        error: 捕获的异常

    Returns:
        结构化错误列表
    """
    error_msg = _get_k8s_error_message(error)
    return [{"status": "error", "message": error_msg}]


def _handle_k8s_single_error(error: Exception) -> dict[str, str]:
    """统一处理 K8s 异常（单条返回）。

    Args:
        error: 捕获的异常

    Returns:
        结构化错误字典
    """
    error_msg = _get_k8s_error_message(error)
    return {"status": "error", "message": error_msg}


def _get_k8s_error_message(error: Exception) -> str:
    """从异常中提取可读的错误信息。

    Args:
        error: 捕获的异常

    Returns:
        格式化的错误描述
    """
    # Kubernetes API 异常
    try:
        from kubernetes.client.exceptions import ApiException

        if isinstance(error, ApiException):
            status_code = error.status
            if status_code == 404:
                return f"K8s 资源不存在: {error.reason or 'Not found'}"
            if status_code == 403:
                return f"K8s 权限不足: {error.reason or 'Forbidden'}"
            return f"K8s API 错误 ({status_code}): {error.reason or str(error)}"
    except ImportError:
        pass

    # 配置异常（kubeconfig 不存在等）
    error_str = str(error).lower()
    if "config" in error_str and ("not found" in error_str or "不存在" in error_str):
        return (
            "Kubernetes 配置未找到，请检查 kubeconfig 路径。"
            "可通过 K8S_KUBECONFIG_PATH 环境变量指定。"
        )
    if "connection" in error_str or "refused" in error_str or "timeout" in error_str:
        return f"Kubernetes 集群连接失败: {error}"

    return f"Kubernetes 操作失败: {error}"


def register_kubernetes_tools(mcp: FastMCP) -> None:
    """向 MCP Server 注册 Kubernetes 管理相关的 Tool。

    Args:
        mcp: FastMCP 实例
    """

    @mcp.tool(
        name="k8s_get_pods",
        description="获取 Kubernetes 集群中指定命名空间的 Pod 状态列表。"
        "返回每个 Pod 的名称、命名空间、运行状态（Running/Pending/Succeeded/Failed/Unknown）、"
        "就绪容器数（ready/total）、重启次数和所在节点。"
        "用于 AI Agent 排查 Pod 运行异常、分析 CrashLoopBackOff 原因、查看调度结果。",
    )
    def _pods_wrapper(
        namespace: Annotated[str, "Kubernetes 命名空间，默认 default"] = "default",
    ) -> list[dict[str, str]]:
        """获取 K8s Pod 列表。"""
        return k8s_get_pods(namespace=namespace)

    @mcp.tool(
        name="k8s_get_deployments",
        description="获取 Kubernetes 集群中指定命名空间的 Deployment 状态列表。"
        "返回每个 Deployment 的名称、命名空间、期望副本数（replicas）和可用副本数（available）。"
        "用于 AI Agent 检查服务部署状态、确认滚动更新是否完成、排查副本数异常。",
    )
    def _deployments_wrapper(
        namespace: Annotated[str, "Kubernetes 命名空间，默认 default"] = "default",
    ) -> list[dict[str, str]]:
        """获取 K8s Deployment 列表。"""
        return k8s_get_deployments(namespace=namespace)

    @mcp.tool(
        name="k8s_get_services",
        description="获取 Kubernetes 集群中指定命名空间的 Service 信息列表。"
        "返回每个 Service 的名称、类型（ClusterIP/NodePort/LoadBalancer）、Cluster IP 和端口映射。"
        "用于 AI Agent 查看服务暴露方式、确认网络连通性、排查服务发现问题。",
    )
    def _services_wrapper(
        namespace: Annotated[str, "Kubernetes 命名空间，默认 default"] = "default",
    ) -> list[dict[str, str]]:
        """获取 K8s Service 列表。"""
        return k8s_get_services(namespace=namespace)

    @mcp.tool(
        name="k8s_logs",
        description="获取指定 Kubernetes Pod 的容器日志。"
        "支持指定命名空间和返回行数（默认 100 行）。"
        "用于 AI Agent 排查 Pod 运行异常、分析应用错误日志。",
    )
    def _logs_wrapper(
        pod_name: Annotated[str, "Pod 名称，必填"],
        namespace: Annotated[str, "Kubernetes 命名空间，默认 default"] = "default",
        lines: Annotated[int, "返回日志的行数，默认 100"] = 100,
    ) -> dict[str, str]:
        """获取 K8s Pod 日志。"""
        return k8s_logs(pod_name=pod_name, namespace=namespace, lines=lines)

    logger.info("Kubernetes 工具注册完毕")