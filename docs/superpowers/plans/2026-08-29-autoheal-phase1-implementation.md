# AutoHeal Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a runnable AutoHeal Phase 1 with Docker Compose, administrator setup/login, encrypted LLM configuration, Ollama/OpenAI-compatible connection testing, and a dark operations console.

**Architecture:** Use a modular FastAPI monolith with SQLAlchemy 2.0 models, a configuration manager, provider-neutral LLM service, and JWT-protected API routes. Use a Vite Vue 3 frontend with Pinia and Axios, served by Nginx and proxying `/api` to the backend. Redis and ChromaDB are included as infrastructure services; Ollama is enabled only by the `local` Compose profile.

**Tech Stack:** Python 3.11+, FastAPI 0.115.0, Uvicorn 0.30.6, SQLAlchemy 2.0.35, Pydantic v2, SQLite/PostgreSQL, Redis 7.x, ChromaDB 0.5.x, LangChain 0.3.0, `langchain-openai` 0.2.0, `langchain-ollama` 0.1.0, Vue 3.4+, TypeScript, Vite 5.x, Element Plus, Pinia, Axios, Docker Compose V2.

## Global Constraints

- Use Pydantic v2 data validation and SQLAlchemy 2.0 APIs.
- Default to SQLite; accept a `DATABASE_URL` environment variable for PostgreSQL.
- Store API keys and Prometheus tokens encrypted with Fernet; never return or log plaintext secrets.
- Use bcrypt/passlib for passwords and JWT for authenticated API calls.
- Return `{code, message, data}` from every JSON API response.
- `local` mode uses Ollama and does not require an API key; cloud modes require an API key.
- Supported mode identifiers are `local`, `openai`, `deepseek`, `qwen`, `azure`, and `zhipu`.
- Use Compose profile `local` for the Ollama service.
- Do not implement LangGraph tools, script execution, SSH, RAG, tickets, ChatOps, or WebSocket alerts in Phase 1.
- Production startup must fail when `SECRET_KEY` or `FERNET_KEY` is absent; development defaults must be explicitly marked for development.
- External provider tests must use mocks and must not require real credentials.

---

### Task 1: Repository Scaffold and Runtime Configuration

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/settings.py`
- Create: `backend/tests/test_settings.py`
- Create: `backend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Create: `.env.example`
- Create: `.gitignore`

**Interfaces:**
- Produce `backend.app.core.settings.Settings`, a Pydantic Settings object with `app_name`, `environment`, `database_url`, `redis_url`, `chroma_url`, `secret_key`, `fernet_key`, `jwt_algorithm`, `jwt_expire_minutes`, `cors_origins`, `llm_*` defaults, and `prometheus_*` defaults.
- Produce `backend.app.main.create_app() -> FastAPI` with a `/api/v1/health` placeholder returning the standard response envelope; later tasks replace the placeholder route.

- [ ] **Step 1: Write failing settings tests**

```python
def test_settings_use_sqlite_and_local_llm_defaults(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)
    assert settings.database_url.startswith("sqlite")
    assert settings.llm_mode == "local"
    assert settings.llm_model == "qwen2.5:7b"

def test_production_requires_explicit_secrets():
    with pytest.raises(ValueError, match="SECRET_KEY"):
        Settings(environment="production", secret_key="", fernet_key="")
```

- [ ] **Step 2: Run `cd backend && pytest tests/test_settings.py -q` and verify it fails because the package is absent.**
- [ ] **Step 3: Implement settings, package metadata, the health placeholder, Dockerfiles, Vite config, `.env.example`, and `.gitignore`.** Keep the backend image command as `uvicorn app.main:app --host 0.0.0.0 --port 8000` and the frontend image as a multi-stage build served by Nginx.
- [ ] **Step 4: Run `cd backend && pytest tests/test_settings.py -q`; expected: PASS.** Run `npm --prefix frontend install` and `npm --prefix frontend run build`; expected: the minimal Vue app builds.
- [ ] **Step 5: Commit**

```bash
git add backend frontend .env.example .gitignore
git commit -m "chore: scaffold phase 1 runtime"
```

### Task 2: Database Models and Security Primitives

**Files:**
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/system_config.py`
- Create: `backend/app/models/audit.py`
- Create: `backend/app/schemas/common.py`
- Create: `backend/tests/test_security.py`
- Create: `backend/tests/test_database.py`

**Interfaces:**
- Produce `get_engine()`, `SessionLocal`, `Base`, and `init_db()` from `database.py`.
- Produce `hash_password(password: str) -> str`, `verify_password(password: str, password_hash: str) -> bool`, `create_access_token(subject: str, role: str, settings: Settings) -> str`, `decode_access_token(token: str, settings: Settings) -> dict`, `encrypt_secret(value: str, settings: Settings) -> str`, and `decrypt_secret(value: str, settings: Settings) -> str`.
- `User` has unique `username`, `password_hash`, `role`, `is_active`, `created_at`, and `updated_at`.
- `SystemConfig` has unique `config_key`, `config_value`, `is_secret`, `category`, `description`, and `updated_at`.
- `AuditLog` stores actor, action, category, success, safe detail, and timestamp.

- [ ] **Step 1: Write failing tests for password hashing, JWT claims/expiry, Fernet round-trip, and SQLite table creation.** Assert that encrypted output differs from plaintext and that invalid JWTs raise a controlled exception.
- [ ] **Step 2: Run `cd backend && pytest tests/test_security.py tests/test_database.py -q`; expected: FAIL with missing modules.**
- [ ] **Step 3: Implement the SQLAlchemy models and security helpers. Prefix encrypted values with `fernet:` so accidental double encryption can be detected. Make `init_db()` idempotent.
- [ ] **Step 4: Run the focused tests; expected: PASS.**
- [ ] **Step 5: Commit**

```bash
git add backend/app/core/database.py backend/app/core/security.py backend/app/models backend/app/schemas/common.py backend/tests
git commit -m "feat: add persistence and security primitives"
```

### Task 3: Configuration Manager and LLM Provider Service

**Files:**
- Create: `backend/app/core/config_manager.py`
- Create: `backend/app/core/llm.py`
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/llm_test.py`
- Create: `backend/tests/test_config_manager.py`
- Create: `backend/tests/test_llm_service.py`

**Interfaces:**
- Produce `DEFAULT_CONFIGS: tuple[dict, ...]` containing all Phase 1 keys and defaults.
- Produce `ConfigManager(session: Session, settings: Settings)` with `seed_defaults()`, `get_all(mask_secrets: bool = True) -> dict[str, dict]`, `get_values() -> dict[str, object]`, and `set_values(values: dict[str, object], actor: str | None = None) -> None`.
- Produce `get_llm(config: Mapping[str, object], settings: Settings | None = None)`, returning `ChatOllama` for `local` and `ChatOpenAI` for API-compatible modes with the configured model, base URL, temperature, max tokens, timeout, and retry count.
- Produce `test_llm_connection(config: Mapping[str, object], settings: Settings) -> dict` with `{ok, provider, message, latency_ms}` and normalized failure categories: `unreachable`, `timeout`, `authentication`, `model_not_found`, and `invalid_configuration`.

- [ ] **Step 1: Write failing tests for default seeding, secret masking, environment fallback, mode validation, local/API factory selection, and mocked connection outcomes.** Verify that local mode accepts an empty key and cloud modes reject one.
- [ ] **Step 2: Run `cd backend && pytest tests/test_config_manager.py tests/test_llm_service.py -q`; expected: FAIL.**
- [ ] **Step 3: Implement configuration persistence and provider selection. Use `httpx` for Ollama `/api/tags` checks and LangChain `ainvoke`/`invoke` only behind the service boundary so tests can mock both network and model calls.
- [ ] **Step 4: Run focused tests; expected: PASS.**
- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config_manager.py backend/app/core/llm.py backend/app/services backend/tests
git commit -m "feat: add dynamic llm configuration"
```

### Task 4: Authentication, Setup, Configuration, and Health APIs

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/app/api/v1/setup.py`
- Create: `backend/app/api/v1/config.py`
- Create: `backend/app/api/v1/dashboard.py`
- Create: `backend/app/api/v1/health.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/setup.py`
- Create: `backend/app/schemas/config.py`
- Create: `backend/app/schemas/dashboard.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/api/__init__.py`
- Create: `backend/tests/api/test_auth_setup.py`
- Create: `backend/tests/api/test_config.py`

**Interfaces:**
- Implement `POST /api/v1/auth/login`, `GET/POST /api/v1/setup`, `GET/PUT /api/v1/config`, `POST /api/v1/config/test/llm`, `GET /api/v1/dashboard/overview`, and `GET /api/v1/health`.
- Produce dependencies `get_db()` and `get_current_user()`; protected endpoints require `Authorization: Bearer <jwt>`.
- Use response helpers `ok(data, message="ok")` and `error(code, message, http_status)` to keep the `{code, message, data}` envelope consistent.
- Setup accepts `username`, `password`, `llm_mode`, `llm_model`, `llm_base_url`, optional `llm_api_key`, numeric tuning values, `prometheus_url`, and `prometheus_token`.

- [ ] **Step 1: Write failing API tests for the full setup/login flow, setup lock after completion, cloud/local validation, masked secrets, unauthorized configuration access, and unified response envelopes.** Use an isolated temporary SQLite database and mock `test_llm_connection`.
- [ ] **Step 2: Run `cd backend && pytest tests/api -q`; expected: FAIL.**
- [ ] **Step 3: Implement dependencies, schemas, routers, transaction boundaries, and application startup initialization. Reject a second setup request with HTTP 409; return HTTP 422 for invalid configuration and HTTP 401 for missing/invalid JWT.
- [ ] **Step 4: Run `cd backend && pytest tests/api -q`; expected: PASS.** Run the entire backend suite with `cd backend && pytest -q`; expected: PASS.
- [ ] **Step 5: Commit**

```bash
git add backend/app backend/tests
git commit -m "feat: add phase 1 management APIs"
```

### Task 5: Vue Console, Setup Wizard, and Settings Interactions

**Files:**
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/api/http.ts`
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/api/config.ts`
- Create: `frontend/src/stores/auth.ts`
- Create: `frontend/src/stores/config.ts`
- Create: `frontend/src/layouts/AppLayout.vue`
- Create: `frontend/src/views/Login.vue`
- Create: `frontend/src/views/Setup.vue`
- Create: `frontend/src/views/Dashboard.vue`
- Create: `frontend/src/views/Settings.vue`
- Create: `frontend/src/views/EmptyModule.vue`
- Create: `frontend/src/styles/theme.css`
- Create: `frontend/src/__tests__/Settings.spec.ts`
- Create: `frontend/vitest.config.ts`
- Modify: `frontend/package.json`

**Interfaces:**
- Axios client adds the JWT bearer token and redirects a 401 response to `/login`.
- `auth` Pinia store exposes `login(credentials)`, `logout()`, `isAuthenticated`, and `currentUser`.
- `config` Pinia store exposes `loadConfig()`, `saveConfig(values)`, and `testLlm(values)`.
- `Settings.vue` and `Setup.vue` share the LLM form model and enforce the local/cloud API-key rule.

- [ ] **Step 1: Write failing Vitest tests for `local` hiding/disabling API Key, cloud modes requiring it, default base URL changes, and test button loading/success/failure state.**
- [ ] **Step 2: Run `npm --prefix frontend run test -- --run`; expected: FAIL because the views and stores do not exist.**
- [ ] **Step 3: Implement the Vue app with Element Plus forms, route guards, dark operations layout, status badges, responsive spacing, and empty states for later modules. Keep labels and actions in plain Chinese suitable for operations staff.
- [ ] **Step 4: Run `npm --prefix frontend run test -- --run`, `npm --prefix frontend run typecheck`, and `npm --prefix frontend run build`; expected: PASS.
- [ ] **Step 5: Commit**

```bash
git add frontend
git commit -m "feat: add setup and configuration console"
```

### Task 6: Docker Compose Integration and Project Documentation

**Files:**
- Create: `docker-compose.yml`
- Modify: `README.md`
- Modify: `.env.example`
- Create: `backend/app/static/.gitkeep`

**Interfaces:**
- Compose service names are `backend`, `frontend`, `redis`, `chromadb`, and profile-gated `ollama`.
- Backend exposes port 8000 internally; frontend exposes port 3000; Redis 6379; ChromaDB 8001; Ollama 11434 under the `local` profile.
- The backend health check calls `http://localhost:8000/api/v1/health`; frontend Nginx proxies `/api/` to `http://backend:8000/api/`.

- [ ] **Step 1: Add Compose and documentation checks**

```bash
docker compose config
test -f backend/Dockerfile
test -f frontend/Dockerfile
rg -n "docker compose|/setup|SECRET_KEY|FERNET_KEY" README.md .env.example
```

- [ ] **Step 2: Run the checks; expected: the Compose file is currently absent and the check fails.**
- [ ] **Step 3: Implement Compose volumes, environment wiring, health checks, the optional Ollama profile, and README instructions for default/local startup, setup, testing, and provider configuration.
- [ ] **Step 4: Run `docker compose config`; expected: PASS.** Build with `docker compose build backend frontend`; expected: both images build when Docker is available.
- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml README.md .env.example backend/app/static/.gitkeep
git commit -m "docs: add compose deployment"
```

### Task 7: End-to-End Verification and Release Check

**Files:**
- Modify: `README.md` only if verification discovers an inaccurate command or endpoint.
- Create: `backend/tests/test_contracts.py` if an uncovered response contract needs a focused regression test.

**Interfaces:**
- No new public interfaces. Verify the contracts from Tasks 1 through 6 together.

- [ ] **Step 1: Run backend tests**

```bash
cd backend && pytest -q
```

Expected: all backend tests pass without network access or real credentials.

- [ ] **Step 2: Run frontend checks**

```bash
npm --prefix frontend run test -- --run
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Expected: all checks pass.

- [ ] **Step 3: Validate Compose**

```bash
docker compose config
```

Expected: valid Compose V2 configuration with the Ollama service under the `local` profile.

- [ ] **Step 4: If Docker is available, start the stack and verify the health endpoint and frontend response.** Use a temporary `.env` with development secrets; do not commit it.
- [ ] **Step 5: Review `git diff --check`, `git status --short --branch`, and the README startup flow. Fix only issues found by these checks.
- [ ] **Step 6: Commit any verification-only fixes**

```bash
git add README.md backend/tests
git commit -m "test: verify phase 1 integration"
```

## Completion Criteria

- A fresh data volume can start the stack and reach `/setup`.
- Setup creates the first administrator and saves all Phase 1 configuration values.
- Local mode checks Ollama model availability without requiring an API key.
- Cloud modes require an API key and use the configured OpenAI-compatible endpoint.
- Login returns a usable JWT; protected endpoints reject missing or invalid tokens.
- Configuration reads mask secrets, and logs/tests contain no plaintext API key or password.
- Settings mode switching updates API-key visibility and validation immediately.
- Dashboard shows installation, current LLM, and dependency health summaries.
- Backend tests, frontend build/type checks, and Compose validation pass.
