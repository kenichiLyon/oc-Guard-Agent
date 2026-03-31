from datetime import datetime, timezone
from typing import Any, Dict, List

from .tool_clients import ToolClients
from .types import Evidence, Incident, LayerResult


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _incident(data: Dict[str, Any]) -> Incident:
    return Incident(
        title=str(data.get("title", "未命名故障")),
        namespace=str(data.get("namespace", "default")),
        service=str(data.get("service", "")),
        symptoms=[str(x) for x in data.get("symptoms", []) if str(x).strip()],
        time_window_minutes=int(data.get("time_window_minutes", 30)),
        suspect_pod=str(data.get("suspect_pod", "")),
    )


def _symptom_layer(inc: Incident) -> LayerResult:
    findings = [f"故障标题：{inc.title}"]
    if inc.symptoms:
        findings.append(f"症状数量：{len(inc.symptoms)}")
    else:
        findings.append("未提供症状，后续证据可能不足")
    return LayerResult(
        layer="现象",
        findings=findings,
        evidences=[Evidence(source="incident", summary="用户输入的故障现象", data={"symptoms": inc.symptoms})],
    )


def _resource_layer(inc: Incident, tools: ToolClients) -> LayerResult:
    findings: List[str] = []
    evidences: List[Evidence] = []
    pods = tools.kubectl(["get", "pods", "-n", inc.namespace, "-o", "wide"])
    evidences.append(Evidence(source="kubectl", summary="Pod 列表", data=pods))
    if pods.get("ok"):
        findings.append("已采集命名空间 Pod 状态")
    else:
        findings.append("Pod 状态采集失败")
    if inc.suspect_pod:
        desc = tools.kubectl(["describe", "pod", inc.suspect_pod, "-n", inc.namespace])
        evidences.append(Evidence(source="kubectl", summary="可疑 Pod 描述", data=desc))
        if desc.get("ok"):
            findings.append("已采集可疑 Pod 详情")
    return LayerResult(layer="资源", findings=findings, evidences=evidences)


def _service_layer(inc: Incident, tools: ToolClients) -> LayerResult:
    findings: List[str] = []
    evidences: List[Evidence] = []
    svcs = tools.kubectl(["get", "svc", "-n", inc.namespace, "-o", "wide"])
    eps = tools.kubectl(["get", "endpoints", "-n", inc.namespace, "-o", "wide"])
    evidences.append(Evidence(source="kubectl", summary="Service 列表", data=svcs))
    evidences.append(Evidence(source="kubectl", summary="Endpoint 列表", data=eps))
    if svcs.get("ok") and eps.get("ok"):
        findings.append("已采集服务与端点拓扑")
    else:
        findings.append("服务拓扑采集不完整")
    return LayerResult(layer="服务", findings=findings, evidences=evidences)


def _dependency_layer(inc: Incident, tools: ToolClients) -> LayerResult:
    findings: List[str] = []
    evidences: List[Evidence] = []
    log_query = " OR ".join(inc.symptoms) if inc.symptoms else "error OR exception OR timeout"
    logs = tools.log_ql(log_query, namespace=inc.namespace, service=inc.service, minutes=inc.time_window_minutes)
    metrics = tools.promql(f'sum(rate(http_requests_total{{namespace="{inc.namespace}"}}[5m]))')
    traces = tools.trace_analyzer(inc.service or inc.namespace, minutes=inc.time_window_minutes)
    evidences.append(Evidence(source="log_ql", summary="日志检索结果", data=logs))
    evidences.append(Evidence(source="promql", summary="关键请求速率", data=metrics))
    evidences.append(Evidence(source="trace_analyzer", summary="链路异常摘要", data=traces))
    if logs.get("ok"):
        findings.append("已采集日志证据")
    else:
        findings.append("日志系统未接通")
    if metrics.get("ok"):
        findings.append("已采集指标证据")
    else:
        findings.append("指标系统未接通")
    if traces.get("ok"):
        findings.append("已采集链路证据")
    else:
        findings.append("链路系统未接通")
    return LayerResult(layer="依赖", findings=findings, evidences=evidences)


def _change_layer(inc: Incident, tools: ToolClients) -> LayerResult:
    findings: List[str] = []
    key_parts = [inc.service, inc.namespace] + inc.symptoms[:3]
    runbooks = tools.runbook_search(key_parts)
    evidences = [Evidence(source="runbook_search", summary="历史方案检索", data=runbooks)]
    if runbooks.get("ok") and runbooks.get("data"):
        findings.append("检索到历史故障方案")
    else:
        findings.append("未检索到可用历史方案")
    return LayerResult(layer="变更", findings=findings, evidences=evidences)


def diagnose(incident_data: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    inc = _incident(incident_data)
    tools = ToolClients(cfg)
    layers = [
        _symptom_layer(inc),
        _resource_layer(inc, tools),
        _service_layer(inc, tools),
        _dependency_layer(inc, tools),
        _change_layer(inc, tools),
    ]
    recommendations: List[str] = []
    if any("采集失败" in f or "未接通" in f for l in layers for f in l.findings):
        recommendations.append("先完成可观测性接入并验证凭据，再执行自动诊断")
    if inc.suspect_pod:
        recommendations.append(f"优先止血：隔离或重启可疑 Pod {inc.suspect_pod}")
    else:
        recommendations.append("优先止血：按错误率最高服务逐步降级或限流")
    recommendations.append("根因确认后更新 runbook，形成可复用处置模板")
    return {
        "meta": {"time": _now(), "engine": "openclaw", "method": "现象->资源->服务->依赖->变更"},
        "incident": incident_data,
        "layers": [x.to_dict() for x in layers],
        "recommendations": recommendations,
    }
