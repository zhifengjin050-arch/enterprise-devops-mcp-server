"""Kubernetes 工具模块测试。

测试 k8s_get_pods、k8s_get_deployments、k8s_get_services、k8s_logs。
使用 mock 避免依赖真实 K8s 集群。
"""

from unittest.mock import MagicMock, patch

import pytest

from app.tools.kubernetes import (
    k8s_get_pods,
    k8s_get_deployments,
    k8s_get_services,
    k8s_logs,
    _get_k8s_error_message,
)


class TestK8sGetPods:
    """k8s_get_pods 测试。"""

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_returns_list_of_dicts(self, mock_get_client: MagicMock) -> None:
        """验证返回列表。"""
        # mock CoreV1Api
        mock_core = MagicMock()
        mock_pod = MagicMock()
        mock_pod.metadata.name = "nginx-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"
        mock_pod.status.container_statuses = []
        mock_pod.spec.node_name = "worker-1"

        mock_core.list_namespaced_pod.return_value.items = [mock_pod]
        mock_get_client.return_value = (mock_core, None, None)

        result = k8s_get_pods(namespace="default")
        assert isinstance(result, list)

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_contains_expected_keys(self, mock_get_client: MagicMock) -> None:
        """验证返回结构包含所有期望字段。"""
        mock_core = MagicMock()
        mock_pod = MagicMock()
        mock_pod.metadata.name = "nginx-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"
        mock_pod.status.container_statuses = []
        mock_pod.spec.node_name = "worker-1"

        mock_core.list_namespaced_pod.return_value.items = [mock_pod]
        mock_get_client.return_value = (mock_core, None, None)

        result = k8s_get_pods(namespace="default")
        expected_keys = {"name", "namespace", "status", "ready", "restarts", "node"}
        assert set(result[0].keys()) == expected_keys

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_pod_status_running(self, mock_get_client: MagicMock) -> None:
        """验证运行中 Pod 的状态。"""
        mock_core = MagicMock()
        mock_pod = MagicMock()
        mock_pod.metadata.name = "nginx-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"
        mock_pod.status.container_statuses = []
        mock_pod.spec.node_name = "worker-1"

        mock_core.list_namespaced_pod.return_value.items = [mock_pod]
        mock_get_client.return_value = (mock_core, None, None)

        result = k8s_get_pods(namespace="default")
        assert result[0]["name"] == "nginx-pod"
        assert result[0]["status"] == "Running"
        assert result[0]["namespace"] == "default"

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_handles_ready_and_restarts(self, mock_get_client: MagicMock) -> None:
        """验证 Ready 计数和重启次数。"""
        mock_core = MagicMock()
        mock_pod = MagicMock()
        mock_pod.metadata.name = "web-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.status.phase = "Running"
        mock_pod.spec.node_name = "node-1"

        # 模拟两个容器，一个就绪一个未就绪，一个有重启
        mock_container1 = MagicMock()
        mock_container1.ready = True
        mock_container1.restart_count = 0

        mock_container2 = MagicMock()
        mock_container2.ready = False
        mock_container2.restart_count = 3

        mock_pod.status.container_statuses = [mock_container1, mock_container2]

        mock_core.list_namespaced_pod.return_value.items = [mock_pod]
        mock_get_client.return_value = (mock_core, None, None)

        result = k8s_get_pods(namespace="default")
        assert result[0]["ready"] == "1/2"
        assert result[0]["restarts"] == "3"

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_handles_k8s_not_connected(self, mock_get_client: MagicMock) -> None:
        """验证 K8s 未连接时返回错误。"""
        mock_get_client.side_effect = Exception("Kubernetes 集群连接失败")

        result = k8s_get_pods(namespace="default")
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["status"] == "error"


class TestK8sGetDeployments:
    """k8s_get_deployments 测试。"""

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_returns_list_of_dicts(self, mock_get_client: MagicMock) -> None:
        """验证返回列表。"""
        mock_apps = MagicMock()
        mock_dep = MagicMock()
        mock_dep.metadata.name = "nginx-deployment"
        mock_dep.metadata.namespace = "default"
        mock_dep.spec.replicas = 3
        mock_dep.status.available_replicas = 3

        mock_apps.list_namespaced_deployment.return_value.items = [mock_dep]
        mock_get_client.return_value = (None, mock_apps, None)

        result = k8s_get_deployments(namespace="default")
        assert isinstance(result, list)

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_contains_expected_keys(self, mock_get_client: MagicMock) -> None:
        """验证返回结构包含所有期望字段。"""
        mock_apps = MagicMock()
        mock_dep = MagicMock()
        mock_dep.metadata.name = "nginx-deployment"
        mock_dep.metadata.namespace = "default"
        mock_dep.spec.replicas = 3
        mock_dep.status.available_replicas = 3

        mock_apps.list_namespaced_deployment.return_value.items = [mock_dep]
        mock_get_client.return_value = (None, mock_apps, None)

        result = k8s_get_deployments(namespace="default")
        expected_keys = {"name", "namespace", "replicas", "available"}
        assert set(result[0].keys()) == expected_keys

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_replica_values(self, mock_get_client: MagicMock) -> None:
        """验证副本数值。"""
        mock_apps = MagicMock()
        mock_dep = MagicMock()
        mock_dep.metadata.name = "api-deployment"
        mock_dep.metadata.namespace = "production"
        mock_dep.spec.replicas = 5
        mock_dep.status.available_replicas = 4

        mock_apps.list_namespaced_deployment.return_value.items = [mock_dep]
        mock_get_client.return_value = (None, mock_apps, None)

        result = k8s_get_deployments(namespace="production")
        assert result[0]["name"] == "api-deployment"
        assert result[0]["replicas"] == "5"
        assert result[0]["available"] == "4"
        assert result[0]["namespace"] == "production"

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_handles_error(self, mock_get_client: MagicMock) -> None:
        """验证异常处理。"""
        mock_get_client.side_effect = Exception("kubeconfig 未找到")

        result = k8s_get_deployments(namespace="default")
        assert result[0]["status"] == "error"


class TestK8sGetServices:
    """k8s_get_services 测试。"""

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_returns_list_of_dicts(self, mock_get_client: MagicMock) -> None:
        """验证返回列表。"""
        mock_core = MagicMock()
        mock_svc = MagicMock()
        mock_svc.metadata.name = "nginx-service"
        mock_svc.metadata.namespace = "default"
        mock_svc.spec.type = "ClusterIP"
        mock_svc.spec.cluster_ip = "10.0.0.1"
        mock_svc.spec.ports = []

        mock_core.list_namespaced_service.return_value.items = [mock_svc]
        mock_get_client.return_value = (mock_core, None, None)

        result = k8s_get_services(namespace="default")
        assert isinstance(result, list)

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_contains_expected_keys(self, mock_get_client: MagicMock) -> None:
        """验证返回结构包含所有期望字段。"""
        mock_core = MagicMock()
        mock_svc = MagicMock()
        mock_svc.metadata.name = "nginx-service"
        mock_svc.metadata.namespace = "default"
        mock_svc.spec.type = "ClusterIP"
        mock_svc.spec.cluster_ip = "10.0.0.1"
        mock_svc.spec.ports = []

        mock_core.list_namespaced_service.return_value.items = [mock_svc]
        mock_get_client.return_value = (mock_core, None, None)

        result = k8s_get_services(namespace="default")
        expected_keys = {"name", "type", "cluster_ip", "ports"}
        assert set(result[0].keys()) == expected_keys

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_service_fields(self, mock_get_client: MagicMock) -> None:
        """验证 Service 字段值。"""
        mock_core = MagicMock()
        mock_svc = MagicMock()
        mock_svc.metadata.name = "web-service"
        mock_svc.metadata.namespace = "default"
        mock_svc.spec.type = "LoadBalancer"
        mock_svc.spec.cluster_ip = "10.0.0.42"
        mock_svc.spec.ports = []

        mock_core.list_namespaced_service.return_value.items = [mock_svc]
        mock_get_client.return_value = (mock_core, None, None)

        result = k8s_get_services(namespace="default")
        assert result[0]["name"] == "web-service"
        assert result[0]["type"] == "LoadBalancer"
        assert result[0]["cluster_ip"] == "10.0.0.42"

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_service_ports(self, mock_get_client: MagicMock) -> None:
        """验证端口解析。"""
        mock_core = MagicMock()
        mock_svc = MagicMock()
        mock_svc.metadata.name = "api-service"
        mock_svc.metadata.namespace = "default"
        mock_svc.spec.type = "NodePort"
        mock_svc.spec.cluster_ip = "10.0.0.2"

        mock_port1 = MagicMock()
        mock_port1.port = 80
        mock_port1.node_port = 30080
        mock_port1.protocol = "TCP"

        mock_port2 = MagicMock()
        mock_port2.port = 443
        mock_port2.node_port = 30443
        mock_port2.protocol = "TCP"

        mock_svc.spec.ports = [mock_port1, mock_port2]

        mock_core.list_namespaced_service.return_value.items = [mock_svc]
        mock_get_client.return_value = (mock_core, None, None)

        result = k8s_get_services(namespace="default")
        assert "80:30080/TCP" in result[0]["ports"]
        assert "443:30443/TCP" in result[0]["ports"]

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_handles_error(self, mock_get_client: MagicMock) -> None:
        """验证异常处理。"""
        mock_get_client.side_effect = Exception("集群连接超时")

        result = k8s_get_services(namespace="default")
        assert result[0]["status"] == "error"


class TestK8sLogs:
    """k8s_logs 测试。"""

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_returns_expected_structure(self, mock_get_client: MagicMock) -> None:
        """验证返回结构。"""
        mock_core = MagicMock()
        mock_core.read_namespaced_pod_log.return_value = "log line 1\\nlog line 2\\n"

        mock_get_client.return_value = (mock_core, None, None)

        result = k8s_logs(pod_name="nginx-pod", namespace="default", lines=100)
        assert isinstance(result, dict)
        assert "pod" in result
        assert "namespace" in result
        assert "logs" in result

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_logs_content(self, mock_get_client: MagicMock) -> None:
        """验证日志内容正确。"""
        mock_core = MagicMock()
        expected_log = "2024/01/15 10:23:45 [error] connect failed\\n"
        mock_core.read_namespaced_pod_log.return_value = expected_log

        mock_get_client.return_value = (mock_core, None, None)

        result = k8s_logs(pod_name="nginx-pod", namespace="default", lines=50)
        assert result["pod"] == "nginx-pod"
        assert result["logs"] == expected_log

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_handles_not_found(self, mock_get_client: MagicMock) -> None:
        """验证 Pod 不存在时返回错误。"""
        from kubernetes.client.exceptions import ApiException

        api_exc = ApiException(status=404, reason="Not Found")
        mock_get_client.side_effect = api_exc

        result = k8s_logs(pod_name="nonexistent-pod", namespace="default")
        assert result["status"] == "error"
        assert "不存在" in result["message"]

    @patch("app.tools.kubernetes._get_k8s_client")
    def test_handles_k8s_not_connected(self, mock_get_client: MagicMock) -> None:
        """验证 K8s 未连接时返回错误。"""
        mock_get_client.side_effect = Exception("Connection refused")

        result = k8s_logs(pod_name="nginx-pod", namespace="default")
        assert result["status"] == "error"

    def test_lines_parameter_default(self) -> None:
        """验证 lines 参数默认值。"""
        # 直接检查函数签名中的默认值
        import inspect

        sig = inspect.signature(k8s_logs)
        lines_param = sig.parameters["lines"]
        assert lines_param.default == 100


class TestK8sErrorMessage:
    """_get_k8s_error_message 测试。"""

    def test_api_exception_404(self) -> None:
        """验证 404 错误。"""
        from kubernetes.client.exceptions import ApiException

        exc = ApiException(status=404, reason="Not Found")
        msg = _get_k8s_error_message(exc)
        assert "不存在" in msg

    def test_api_exception_403(self) -> None:
        """验证 403 错误。"""
        from kubernetes.client.exceptions import ApiException

        exc = ApiException(status=403, reason="Forbidden")
        msg = _get_k8s_error_message(exc)
        assert "权限不足" in msg

    def test_api_exception_other(self) -> None:
        """验证其他 HTTP 错误。"""
        from kubernetes.client.exceptions import ApiException

        exc = ApiException(status=500, reason="Internal Server Error")
        msg = _get_k8s_error_message(exc)
        assert "500" in msg

    def test_config_not_found(self) -> None:
        """验证 kubeconfig 未找到。"""
        exc = FileNotFoundError("config file not found")
        msg = _get_k8s_error_message(exc)
        assert "kubeconfig" in msg

    def test_connection_refused(self) -> None:
        """验证连接被拒绝。"""
        exc = ConnectionRefusedError("Connection refused")
        msg = _get_k8s_error_message(exc)
        assert "连接失败" in msg

    def test_generic_error(self) -> None:
        """验证通用错误。"""
        exc = RuntimeError("something went wrong")
        msg = _get_k8s_error_message(exc)
        assert "操作失败" in msg


class TestK8sPermission:
    """Kubernetes 权限测试。"""

    def test_k8s_tools_are_read_only(self) -> None:
        """验证 K8s tools 分类为 READ_ONLY。"""
        from app.security.permission import PermissionManager

        pm = PermissionManager()
        assert pm.classify_operation("k8s_get_pods") != "execute"
        assert pm.classify_operation("k8s_get_deployments") != "execute"
        assert pm.classify_operation("k8s_get_services") != "execute"
        assert pm.classify_operation("k8s_logs") != "execute"

    def test_kubernetes_module_in_whitelist(self) -> None:
        """验证 kubernetes 在模块白名单中。"""
        from app.config import settings

        allowed = settings.get_allowed_tools_list()
        assert "kubernetes" in allowed

    def test_k8s_tools_in_read_only_list(self) -> None:
        """验证 k8s tools 在只读工具列表中。"""
        from app.config import settings

        read_only = settings.get_read_only_tools_list()
        assert "k8s_get_pods" in read_only
        assert "k8s_get_deployments" in read_only
        assert "k8s_get_services" in read_only
        assert "k8s_logs" in read_only


class TestK8sRegistration:
    """K8s 注册测试。"""

    def test_four_tools_registered(self) -> None:
        """验证注册了 4 个 Tool。"""
        import asyncio
        from fastmcp import FastMCP
        from app.tools.kubernetes import register_kubernetes_tools

        mcp = FastMCP("test")
        register_kubernetes_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        assert len(tools) == 4

    def test_all_tool_names(self) -> None:
        """验证所有 Tool 名称正确。"""
        import asyncio
        from fastmcp import FastMCP
        from app.tools.kubernetes import register_kubernetes_tools

        mcp = FastMCP("test")
        register_kubernetes_tools(mcp)

        tools = asyncio.run(mcp.list_tools())
        names = [t.name for t in tools]
        assert "k8s_get_pods" in names
        assert "k8s_get_deployments" in names
        assert "k8s_get_services" in names
        assert "k8s_logs" in names