# AutoHeal

AutoHeal 是一个基于 LangChain Agent 的智能运维平台：接收 Prometheus 告警，由 AI 分析并执行可审计的修复动作。项目支持 Ollama 本地模型和 OpenAI-compatible 云端 API，配置通过控制台完成。

当前仓库交付的是 Phase 1：运行骨架、首次安装、管理员登录、LLM 配置中心和依赖健康概览。告警闭环、脚本执行、工单和 ChatOps 会在后续阶段接入。

## 快速启动

需要 Docker Engine、Docker Compose V2 和可访问的 Docker/PyPI/npm 镜像。

```bash
git clone https://github.com/pro-xiaowu/AutoHeal.git
cd AutoHeal
cp .env.example .env
docker compose up -d --build
```

打开 <http://localhost:3000>。首次启动会进入 `/setup`，填写管理员账号、LLM 模式和模型名称后完成初始化。之后使用管理员账号从 `/login` 登录。

使用 Ollama 本地模式时：

```bash
docker compose --profile local up -d --build
docker compose exec ollama ollama pull qwen2.5:7b
```

然后在 Setup 或 Settings 中选择 `Ollama 本地`，模型填 `qwen2.5:7b`。本地模式不需要 API Key。

## 云端 LLM

Settings 支持 `openai`、`deepseek`、`qwen`、`azure` 和 `zhipu`。云端模式必须填写 API Key，Base URL 和模型名称可以覆盖默认值。API Key 使用 Fernet 加密保存在数据库，读取接口只返回掩码。

项目使用 `langchain-ollama==0.2.0` 而不是最初的 `0.1.0`：后者与 `langchain==0.3.0` 的 `langchain-core` 依赖约束冲突，无法在全新环境安装。其余核心版本保持计划约束。

## 环境变量

复制 `.env.example` 为 `.env` 后修改：

- `SECRET_KEY`：JWT 签名密钥。
- `FERNET_KEY`：必须是 32 字节的 URL-safe Base64 Fernet 密钥；生产环境必须替换开发示例。
- `DATABASE_URL`：默认 SQLite，可改为 PostgreSQL 连接串。
- `LLM_MODE`、`LLM_MODEL`、`LLM_BASE_URL`：首次 Setup 的默认值。
- `LLM_API_KEY`：可选的云端模式初始密钥，保存后会加密。
- `PROMETHEUS_URL`、`PROMETHEUS_TOKEN`：后续告警接入的默认值。

所有配置都可以在 `/settings` 修改，修改后即时生效，不需要重启容器。

## 开发验证

后端：

```bash
python3 -m pip install -r backend/requirements.txt
cd backend
pytest -q
```

前端：

```bash
npm --prefix frontend install
npm --prefix frontend run test -- --run
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Compose 配置：

```bash
docker compose config
curl http://localhost:8000/api/v1/health
```

## Phase 1 API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/auth/login` | 管理员登录并获取 JWT |
| GET/POST | `/api/v1/setup` | 查询和完成首次安装 |
| GET/PUT | `/api/v1/config` | 读取和更新配置（JWT） |
| POST | `/api/v1/config/test/llm` | 测试当前 LLM（JWT） |
| GET | `/api/v1/dashboard/overview` | 查看系统概览（JWT） |
| GET | `/api/v1/health` | 容器健康检查 |

JSON 接口统一返回 `{code, message, data}`。敏感值不会出现在响应、异常消息或日志中。

## 项目结构

```text
backend/        FastAPI、SQLAlchemy、配置管理和 LLM 服务
frontend/       Vue 3、Element Plus、Pinia 控制台
docker-compose.yml
docs/           设计文档和实现计划
data/           Compose 运行时 SQLite 数据（不提交）
```

## 开源协议

MIT License，详见 [LICENSE](LICENSE)。
