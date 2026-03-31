# OpenClaw Agent

## 项目目标

本项目已完成从 CloudConfigGuard 到 OpenClaw 的迁移，当前只保留 OpenClaw 诊断能力。
项目提供两种使用方式：CLI 诊断器与 MCP Server，不提供 WebUI。
其中 openclaw-agent 是对 openclaw 核心诊断引擎的工程化封装：CLI 直接调用 openclaw，MCP Server 则把同一套诊断能力暴露给外部客户端。

诊断方法固定为五层链路：

1. 现象
2. 资源
3. 服务
4. 依赖
5. 变更

并通过以下工具源采集证据：

- kubectl
- promql
- log_ql
- trace_analyzer
- runbook_search

## 安装与启动

```bash
pip install -e .
openclaw --config examples/openclaw.config.json --incident-file examples/incidents/pod_crashloop.json --format pretty
```

也可以使用项目同名入口：

```bash
openclaw-agent --config examples/openclaw.config.json --incident-file examples/incidents/pod_crashloop.json --format pretty
```

## MCP 模式

启动 MCP Server：

```bash
openclaw-mcp
```

项目同名入口也可直接使用：

```bash
openclaw-agent-mcp
```

也可以使用以下等价方式启动：

```bash
python -m openclaw.mcp_main
python mcp_main.py
```

当前暴露一个工具：

- `openclaw_agent_diagnose`
- `openclaw_diagnose`（兼容旧名称）

工具输入：

- `incident`
- `config_path`（可选，不传时默认读取内置 `default_config.json`，也可通过 `OPENCLAW_CONFIG` 指定）

工具输出：

- `structuredContent`
- `content`
- `isError`

## 调用方式

### 1) 使用 incident 文件

```bash
openclaw --config examples/openclaw.config.json --incident-file examples/incidents/pod_crashloop.json
```

### 2) 直接传 incident JSON

```bash
openclaw --config examples/openclaw.config.json --incident-json "{\"title\":\"api 5xx\",\"namespace\":\"default\",\"service\":\"api\",\"symptoms\":[\"5xx\",\"timeout\"],\"time_window_minutes\":30}" --format json
```

参数说明：

- `--config`：OpenClaw 配置文件
- `--incident-file`：故障输入文件
- `--incident-json`：故障输入 JSON 文本
- `--format`：`pretty` 或 `json`

## MCP 客户端配置示例

Claude Desktop 或其他支持 stdio MCP 的客户端可配置为：

```json
{
  "mcpServers": {
    "openclaw": {
      "command": "openclaw-agent-mcp",
      "env": {
        "OPENCLAW_CONFIG": "G:/your-path/OpenClaw-Agent/examples/openclaw.config.json"
      }
    }
  }
}
```

如果未全局安装脚本，也可以直接使用 Python：

```json
{
  "mcpServers": {
    "openclaw": {
      "command": "python",
      "args": ["-m", "openclaw.mcp_main"],
      "cwd": "G:/your-path/OpenClaw-Agent",
      "env": {
        "OPENCLAW_CONFIG": "G:/your-path/OpenClaw-Agent/examples/openclaw.config.json"
      }
    }
  }
}
```

## 配置说明

默认样例配置文件为：

`examples/openclaw.config.json`

核心字段：

- `mock_mode`：是否使用模拟数据
- `kubectl_bin`：kubectl 可执行文件
- `command_timeout_sec`：命令超时秒数
- `http_timeout_sec`：HTTP 超时秒数
- `promql_endpoint`：指标查询接口
- `log_ql_endpoint`：日志查询接口
- `trace_endpoint`：链路分析接口
- `runbook_endpoint`：runbook 检索接口

## 示例 incident

`examples/incidents/pod_crashloop.json`

字段包括：

- `title`
- `namespace`
- `service`
- `symptoms`
- `time_window_minutes`
- `suspect_pod`

## 测试

```bash
python -m pytest -q
```
