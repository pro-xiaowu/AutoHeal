# AutoHeal 第一阶段设计：基础骨架与配置中心

## 1. 目标与范围

第一阶段交付一个可运行、可部署、可验收的 AutoHeal 基础版本。用户通过 Docker Compose 启动服务，打开 Vue 控制台，完成首次安装，配置并测试本地 Ollama 或云端 OpenAI-compatible LLM，登录后查看 Dashboard 和系统状态。

本阶段包含：

- FastAPI 后端、Vue 3 + TypeScript + Element Plus 前端和 Docker Compose 部署骨架。
- SQLite 默认数据库，并保留通过环境变量切换 PostgreSQL 的能力。
- Redis、ChromaDB 基础服务接入和健康状态展示。
- 管理员登录、JWT 鉴权和首次安装向导。
- LLM 双模式配置：Ollama 本地模式和 OpenAI-compatible API 模式。
- LLM 配置的加密存储、掩码读取、动态校验和连接测试。
- Prometheus URL/token 的可视化配置存储，为后续告警接收做准备。
- 深色运维控制台的 Dashboard、Settings、Setup 和导航空状态页。
- 后端单元/API 测试、前端构建检查和 Compose 健康检查。

本阶段不实现 LangGraph 多工具 Agent、脚本执行沙箱、SSH 执行、RAG、工单流转、ChatOps 多轮会话、WebSocket 告警推送和生产级权限细分。这些功能分别在后续阶段实现，但本阶段会保留清晰的模块边界和导航入口。

## 2. 架构

```text
浏览器
  │
  ▼
Vue 3 + Element Plus + Pinia
  │ Axios / JWT
  ▼
FastAPI
  ├── auth       登录与 JWT
  ├── setup      安装状态与初始化
  ├── config     配置读写与测试连接
  ├── dashboard  系统概览
  └── health     容器健康检查
       │
       ├── SQLAlchemy 2.0 → SQLite / PostgreSQL
       ├── Redis → 会话和短期状态
       ├── ChromaDB → 后续 RAG 的基础服务
       └── LLM Adapter → Ollama / OpenAI-compatible API
```

采用模块化单体。后端按 `api`、`core`、`models`、`services`、`utils` 分层，前端按视图、组件、API 客户端、stores 和样式分层。第一阶段不拆分微服务，以降低部署和调试复杂度；后续执行器或 Agent 可以沿这些边界独立拆出。

## 3. 启动和数据流

1. 后端启动时读取环境变量，创建数据库表，并将数据库中不存在的默认配置导入 `system_config`。
2. 前端调用 `GET /api/v1/setup`。如果 `setup_completed` 不为真，路由重定向到 `/setup`。
3. 用户提交管理员账号、LLM 配置和 Prometheus 基础配置。后端校验字段、测试 LLM（如果用户请求测试），在一个事务中创建管理员并保存配置，最后设置 `setup_completed=true`。
4. 后端签发 JWT，前端保存登录状态并进入 `/dashboard`。
5. 后续 Settings 修改立即写入数据库；LLM 工厂每次按最新配置创建实例，无需重启容器。
6. Dashboard 聚合数据库配置和 Redis、ChromaDB、Ollama/LLM 的可达性，展示健康状态和配置摘要。

## 4. 数据模型

### `users`

- `id`：整数主键。
- `username`：唯一、非空。
- `password_hash`：使用 bcrypt/passlib 保存，不保存明文密码。
- `role`：第一阶段默认为 `admin`。
- `is_active`：布尔值，默认 true。
- `created_at`、`updated_at`：UTC 时间。

### `system_config`

- `id`：整数主键。
- `config_key`：唯一、非空。
- `config_value`：文本值；敏感值保存为 Fernet 加密内容。
- `is_secret`：标记是否为敏感配置。
- `category`：`ai_engine`、`alert_source` 或 `system`。
- `description`：面向管理界面的说明。
- `updated_at`：UTC 更新时间。

第一阶段初始化配置键：

| 键 | 默认值 | secret | 分类 |
| --- | --- | --- | --- |
| `setup_completed` | `false` | 否 | `system` |
| `llm_mode` | `local` | 否 | `ai_engine` |
| `llm_model` | `qwen2.5:7b` | 否 | `ai_engine` |
| `llm_base_url` | `http://ollama:11434` | 否 | `ai_engine` |
| `llm_api_key` | 空 | 是 | `ai_engine` |
| `llm_temperature` | `0.1` | 否 | `ai_engine` |
| `llm_max_tokens` | `2048` | 否 | `ai_engine` |
| `llm_timeout` | `60` | 否 | `ai_engine` |
| `llm_max_retries` | `3` | 否 | `ai_engine` |
| `prometheus_url` | 空 | 否 | `alert_source` |
| `prometheus_token` | 空 | 是 | `alert_source` |

环境变量作为数据库缺失配置的兜底，并只导入一次。数据库已有值优先于环境变量。

## 5. 后端模块

- `app/main.py`：应用创建、路由注册、启动初始化和 CORS。
- `app/core/config.py`：Pydantic Settings、数据库 URL、JWT 密钥、Fernet 密钥和 CORS 配置。
- `app/core/database.py`：SQLAlchemy engine、session 和表初始化。
- `app/core/security.py`：bcrypt 密码哈希、JWT 签发/解析、Fernet 加解密。
- `app/core/llm.py`：统一 `get_llm(config)` 工厂；本地模式使用 `ChatOllama`，云端模式使用 `ChatOpenAI`，DeepSeek/Qwen/Zhipu/Azure 使用对应的 OpenAI-compatible base URL 和模型配置。
- `app/core/config_manager.py`：默认配置导入、配置读取/掩码、敏感值保存和环境变量兜底。
- `app/services/llm_test.py`：连接测试，隔离供应商差异并归一化错误。
- `app/api/v1/auth.py`、`setup.py`、`config.py`、`dashboard.py`、`health.py`：第一阶段 HTTP 接口。
- `app/models/user.py`、`config.py`、`audit.py`：数据模型。
- `app/schemas/`：Pydantic v2 请求和响应模型。

所有 API 使用统一响应结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": {}
}
```

错误响应按 401、403、404、422、500 分类。错误消息可指导用户修复配置，但不包含 API Key、密码、Authorization 或完整第三方响应。

## 6. API 合约

- `POST /api/v1/auth/login`：校验用户名和密码，返回 JWT 与用户摘要；初始化前也可用于登录已创建的管理员。
- `GET /api/v1/setup`：返回 `setup_completed`、默认值和服务端版本；不返回任何秘密原文。
- `POST /api/v1/setup`：仅在未完成初始化时可调用；创建管理员、保存初始配置并完成安装。重复调用返回冲突错误。
- `GET /api/v1/config`：按分类返回配置；secret 字段返回 `is_set` 和掩码，不返回原文。
- `PUT /api/v1/config`：JWT 保护，支持部分更新；secret 字段只有在请求显式提供新值时才更新。
- `POST /api/v1/config/test/llm`：JWT 保护，按请求配置或当前保存配置测试 LLM，不持久化测试参数。
- `GET /api/v1/dashboard/overview`：JWT 保护，返回当前模式、模型、安装状态和依赖服务状态。
- `GET /api/v1/health`：无需登录，返回后端和数据库基础状态，供 Docker 健康检查使用。

LLM 模式枚举为 `local`、`openai`、`deepseek`、`qwen`、`azure`、`zhipu`。`local` 检查 Ollama `/api/tags` 并确认目标模型存在；其他模式发送最小测试消息。每个请求都有可配置的 timeout 和重试上限。

## 7. 前端体验

前端使用 Vue 3 Composition API、`<script setup>`、TypeScript、Element Plus 和 Pinia。整体采用深色 Grafana 风格，但使用青绿色状态色、琥珀警告色和冷白文字区分信息层级。

路由：

- `/login`：登录表单和错误状态。
- `/setup`：首次安装向导，管理员、AI 引擎、告警源分组展示。
- `/dashboard`：服务状态、当前模型、安装摘要和待实现模块入口。
- `/settings`：AI 引擎、告警源、系统配置编辑。
- `/scripts`、`/tickets`、`/chat`：带空状态的导航占位页，后续阶段填充。

Settings 的联动规则：

- `local` 模式隐藏或禁用 API Key，并移除必填校验，显示“本地模式无需 API Key”。
- 云端模式显示 API Key 并要求填写；已保存密钥只显示掩码。
- Base URL 根据模式填入默认值但可覆盖。
- 温度使用 0 到 1 的滑块；最大 token、超时和重试次数使用数字输入。
- 测试按钮具备加载、成功和失败状态；保存成功后刷新摘要，不重启服务。

## 8. 部署

根目录提供 Docker Compose V2 配置：

- `backend`：FastAPI/Uvicorn，内部端口 8000。
- `frontend`：Vue 构建产物由 Nginx 提供，端口 3000。
- `redis`：`redis:7-alpine`，端口 6379。
- `chromadb`：Chroma 0.5.x，端口 8001。
- `ollama`：`ollama/ollama`，profile 为 `local`，端口 11434。

默认命令为 `docker compose up -d`；需要本地模型时使用 `docker compose --profile local up -d`。SQLite 数据、上传目录和加密密钥必须通过卷或环境变量持久化。前端 Nginx 将 `/api` 反向代理到后端。

## 9. 安全和失败处理

- API Key、Prometheus token 和密码从日志、响应和异常中剔除。
- 生产环境缺少 `SECRET_KEY` 或 Fernet 密钥时后端拒绝启动；开发默认值必须显式标记为开发用途。
- 配置写入使用数据库事务；唯一键冲突转换为可读的冲突响应。
- LLM 测试区分服务不可达、超时、认证失败和模型不存在，前端只展示必要信息。
- Setup 端点在安装完成后锁定；只有 JWT 用户可以修改配置。
- 数据库不可用时启动失败并记录原因，避免以半初始化状态提供服务。

## 10. 验收与测试

后端：

- 加密/解密和密码哈希单元测试。
- 配置默认值导入、secret 掩码、环境变量兜底测试。
- LLM 工厂和 Ollama/OpenAI 测试服务 mock。
- 登录、首次设置、Setup 锁定、未授权访问、配置更新和统一错误格式 API 测试。

前端：

- TypeScript 类型检查和生产构建。
- Settings 模式切换、API Key 必填联动、测试连接状态和错误提示测试。

交付验证命令至少包括后端测试、前端 `npm run build`、Compose 配置校验和健康接口请求。验收通过条件是：全新数据卷启动后可完成 Setup；local 模式可检测 Ollama 模型；云端模式可用 mock 完成测试；登录后可查看 Dashboard、读取/修改配置；密钥不会出现在接口响应和日志中。

## 11. 后续阶段接口预留

第一阶段保留 `alerts`、`agent`、`scripts`、`executions`、`tickets` 和 `chat` 的路由/模块边界，不提前实现复杂业务。第二阶段将接入 Prometheus Webhook、LangGraph Agent 和 SSE；第三阶段加入脚本执行安全控制；第四阶段加入工单、Dashboard 指标和 ChatOps；第五阶段完成 PostgreSQL 迁移、权限、审计和生产化增强。
