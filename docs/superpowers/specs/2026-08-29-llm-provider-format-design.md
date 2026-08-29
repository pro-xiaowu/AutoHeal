# AutoHeal LLM 服务商与 API 格式设计

## 背景

当前配置字段 `llm_mode` 同时表达服务商、本地/云端模式和请求协议，无法准确覆盖 OpenAI-compatible、Anthropic Messages、Ollama 等不同接口。新设计将服务商和 API 格式拆分，并为模型名称提供自动发现与手动回退。

## 目标

- 将 LLM 配置拆分为服务商和 API 格式两个独立维度。
- 支持 Ollama、OpenAI、Anthropic、DeepSeek、通义千问、智谱和自定义网关。
- 自动获取可用模型，获取失败时仍允许手动输入。
- 默认使用 Chat 调用；仅在协议和供应商明确支持时提供 Responses。
- 保持 API Key 加密存储、掩码读取和统一错误响应。
- 兼容 Phase 1 已存在的 `llm_mode` 配置，不要求用户清空数据库。

## 配置模型

新增配置键：

| 键 | 值 | 说明 |
| --- | --- | --- |
| `llm_provider` | `ollama` / `openai` / `anthropic` / `deepseek` / `qwen` / `zhipu` / `custom` | 服务商标识 |
| `llm_api_format` | `ollama` / `openai_chat` / `openai_responses` / `anthropic_messages` | 请求协议 |
| `llm_model` | 字符串 | 模型或部署名称 |
| `llm_base_url` | URL | 服务地址，可覆盖默认值 |
| `llm_api_key` | 加密字符串 | API Key，本地模式可为空 |

旧配置兼容规则：

- `llm_mode=local` 映射为 `llm_provider=ollama`、`llm_api_format=ollama`。
- `llm_mode=openai/deepseek/qwen/zhipu` 映射为同名服务商和 `openai_chat` 格式。
- `llm_mode=azure` 不再支持；启动迁移时转换为 `custom`，要求用户重新选择格式、地址和模型。
- 旧键保留只读兼容一段时间，前端不再展示；新写入只使用新键。

默认服务商与格式：

| 服务商 | 默认格式 | 默认地址 |
| --- | --- | --- |
| ollama | `ollama` | `http://ollama:11434` |
| openai | `openai_chat` | `https://api.openai.com/v1` |
| anthropic | `anthropic_messages` | `https://api.anthropic.com` |
| deepseek | `openai_chat` | `https://api.deepseek.com/v1` |
| qwen | `openai_chat` | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| zhipu | `openai_chat` | `https://open.bigmodel.cn/api/paas/v4` |
| custom | 用户选择 | 用户填写 |

允许的服务商/格式组合：

| 服务商 | 可选格式 |
| --- | --- |
| ollama | `ollama` |
| openai | `openai_chat`、`openai_responses` |
| anthropic | `anthropic_messages` |
| deepseek | `openai_chat` |
| qwen | `openai_chat` |
| zhipu | `openai_chat` |
| custom | `openai_chat`、`openai_responses`、`anthropic_messages` |

## 后端接口

### 模型发现

新增受 JWT 保护的接口：

```text
POST /api/v1/config/models/discover
```

请求体使用与连接测试相同的 `values` 结构，允许使用前端尚未保存的 provider、format、Base URL、模型和 API Key。掩码值 `********` 或省略的 API Key 会复用数据库中已保存的密钥。返回统一结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "ok": true,
    "provider": "openai",
    "api_format": "openai_chat",
    "models": ["gpt-4o-mini"],
    "manual_input": false,
    "category": "ok"
  }
}
```

发现策略：

- `ollama` 请求 `<base_url>/api/tags`，读取 `models[].name`。
- `openai_chat` 和 `openai_responses` 请求 `<base_url>/models`，使用 Bearer API Key。
- `anthropic_messages` 尝试 `<base_url>/v1/models`，使用 `x-api-key` 和 Anthropic 版本请求头；服务商不支持时返回手动输入状态。
- HTTP 认证、超时、网络和解析错误都返回安全的错误类别，不返回 API Key 或完整异常内容。
- 空列表或不支持的模型接口不会阻塞保存，前端进入手动输入模式。

### LLM 工厂与连接测试

根据 `llm_api_format` 选择 LangChain 实现：

- `ollama` 使用 `ChatOllama`。
- `openai_chat` 使用 `ChatOpenAI` 的 Chat Completions 调用。
- `openai_responses` 使用独立的 Responses 协议适配器调用 `/responses`，不依赖当前版本 `ChatOpenAI` 的未提供参数，仅允许 `openai` 或 `custom` 服务商。
- `anthropic_messages` 使用 `ChatAnthropic`。

后端新增与现有 LangChain 0.3 依赖兼容的固定版本 `langchain-anthropic`。Responses 适配器通过 `httpx` 调用协议，不要求升级现有 `langchain-openai`。

连接测试和模型发现共用 provider/format 校验。云端格式必须有 API Key；Ollama 不要求 API Key。Responses 只允许 OpenAI 和 Custom 服务商，其他组合返回 `invalid_configuration`。

## 前端交互

Settings 和 Setup 共用配置表单：

1. 先选择服务商。
2. 根据服务商显示可用 API 格式，自动填充默认格式和 Base URL。
3. 点击“刷新模型”调用模型发现接口。
4. 获取成功且列表非空时只显示模型下拉框。
5. 获取失败显示错误状态和文本输入框，用户仍可继续保存。
6. 获取成功但列表为空时视为无法获取，切换到文本输入框。
7. `ollama` 隐藏 API Key；其他需要密钥的服务商显示必填 API Key。
8. `openai_responses` 只在 `openai` 和 `custom` 服务商下可见。

表单状态不会把掩码值 `********` 当成新密钥提交；空白密钥表示保留已保存密钥。

## 数据迁移与安全

- 应用启动时对已存在配置执行一次幂等映射，不删除旧配置记录。
- 新配置写入沿用 Fernet 加密和 `fernet:` 前缀。
- 日志、错误消息和接口响应不包含 API Key、密码或完整供应商异常。
- Azure 不再作为可选服务商；历史 Azure 配置迁移为 `custom` 未完成状态，避免静默调用错误地址。

## 测试范围

后端：

- provider/format 组合校验和默认值。
- 旧 `llm_mode` 映射和 Azure 迁移。
- Ollama、OpenAI-compatible、Anthropic 模型列表解析，使用 HTTP mock。
- 模型发现超时、认证失败、空列表和不支持接口时的手动回退。
- Chat、Responses、Anthropic、Ollama 工厂选择。
- API Key 加密、掩码和保留语义。

前端：

- 服务商改变时格式和 Base URL 联动。
- Responses 仅在允许的服务商/格式组合下显示。
- 模型刷新成功、失败、空列表和手动输入状态。
- Ollama 隐藏 API Key，云端模式校验 API Key。
- Setup 与 Settings 使用同一套表单规则。

## 非目标

- 本阶段不实现 Agent、LangGraph Tools、脚本执行、SSH、RAG、工单、ChatOps 或告警 WebSocket。
- 不为每个供应商维护静态模型白名单；模型列表以服务端返回为准，仅在发现失败或返回空列表时使用手动输入。
