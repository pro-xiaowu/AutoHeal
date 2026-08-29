# AutoHeal LLM Provider and API Format Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split LLM configuration into provider and API format, add model discovery with manual fallback, and support Ollama, OpenAI Chat/Responses, Anthropic Messages, DeepSeek, Qwen, Zhipu, and custom gateways.

**Architecture:** Keep the existing FastAPI modular monolith and SQLAlchemy configuration store. Add provider/format normalization and migration in `ConfigManager`, isolate model discovery and protocol adapters behind service boundaries, and expose protected Settings plus pre-setup Setup discovery endpoints. Replace the single frontend mode selector with provider and format selectors plus a model discovery state machine shared by Setup and Settings.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy 2.0, httpx, LangChain 0.3, `langchain-openai`, `langchain-anthropic==0.2.4`, `langchain-ollama`, Vue 3, TypeScript, Element Plus, Pinia, Vitest with `happy-dom`, Docker Compose.

## Global Constraints

- Provider values are `ollama`, `openai`, `anthropic`, `deepseek`, `qwen`, `zhipu`, and `custom`; Azure is removed from active choices, validation, defaults, and documentation (historical Azure may appear only in migration code/tests).
- Format values are `ollama`, `openai_chat`, `openai_responses`, and `anthropic_messages`.
- Allowed combinations are: Ollama/ollama; OpenAI/openai_chat or openai_responses; Anthropic/anthropic_messages; DeepSeek/Qwen/Zhipu/openai_chat; Custom/openai_chat, openai_responses, or anthropic_messages.
- Ollama model discovery uses `/api/tags`; OpenAI-compatible discovery uses `/models`; Anthropic discovery uses `/v1/models` with `x-api-key` and an Anthropic version header.
- Model discovery failure or an empty model list must switch the UI to a manual text input without blocking save.
- `openai_responses` uses a dedicated HTTP protocol adapter because the pinned `langchain-openai==0.2.0` does not expose a Responses option; this phase implements `invoke`, not streaming.
- API keys remain Fernet-encrypted in SQLite and masked as `********`; blank masked fields preserve existing secrets.
- Every JSON API response uses `{code, message, data}` and provider errors never expose credentials or raw exception text.
- Existing `llm_mode` rows remain readable. Migrations are idempotent and do not require deleting the database.

---

### Task 1: Provider/Format Configuration Model and Migration

**Files:**
- Modify: `backend/app/core/config_manager.py`
- Modify: `backend/app/schemas/config.py`
- Modify: `backend/app/schemas/setup.py`
- Modify: `backend/app/api/v1/setup.py`
- Modify: `backend/app/api/v1/config.py`
- Modify: `backend/app/api/v1/dashboard.py`
- Modify: `backend/app/core/settings.py`
- Test: `backend/tests/test_config_manager.py`
- Test: `backend/tests/api/test_auth_setup.py`
- Test: `backend/tests/api/test_config.py`

**Interfaces:**
- Add module-level `normalize_provider_format(values: Mapping[str, object]) -> dict[str, object]` and `validate_provider_format(values: Mapping[str, object]) -> None` in `app.core.config_manager`; later modules import these exact names.
- Add `ConfigManager.migrate_legacy_mode(existing_keys: set[str]) -> None`, called by `seed_defaults()` before canonical defaults are inserted.
- `llm_provider` and `llm_api_format` become the canonical persisted values; `llm_mode` is retained only for read compatibility.
- Setup and configuration update payloads accept `llm_provider` and `llm_api_format`; new API writes reject `llm_mode` and Azure.

- [ ] **Step 1: Write failing tests for canonical defaults and legacy mapping.**

```python
def test_legacy_local_mode_maps_to_ollama(tmp_path):
    manager, session = make_manager(tmp_path)
    session.add(SystemConfig(config_key="llm_mode", config_value="local", is_secret=False, category="ai_engine"))
    session.commit()
    manager.seed_defaults()
    values = manager.get_values()
    assert values["llm_provider"] == "ollama"
    assert values["llm_api_format"] == "ollama"


def test_legacy_azure_mode_requires_custom_reconfiguration(tmp_path):
    manager, session = make_manager(tmp_path)
    session.add(SystemConfig(config_key="llm_mode", config_value="azure", is_secret=False, category="ai_engine"))
    session.commit()
    manager.seed_defaults()
    values = manager.get_values()
    assert values["llm_provider"] == "custom"
    assert values["llm_api_format"] == "openai_chat"
    assert values["llm_migration_required"] is True
```

- [ ] **Step 2: Run `python3 -m pytest -q backend/tests/test_config_manager.py backend/tests/api/test_auth_setup.py backend/tests/api/test_config.py`; verify the new tests fail because the new keys and migration do not exist.**
- [ ] **Step 3: Add canonical defaults and implement migration before default seeding.**

```python
PROVIDER_FORMATS = {
    "ollama": {"ollama"},
    "openai": {"openai_chat", "openai_responses"},
    "anthropic": {"anthropic_messages"},
    "deepseek": {"openai_chat"},
    "qwen": {"openai_chat"},
    "zhipu": {"openai_chat"},
    "custom": {"openai_chat", "openai_responses", "anthropic_messages"},
}

LEGACY_MODE_MAP = {
    "local": ("ollama", "ollama", False),
    "openai": ("openai", "openai_chat", False),
    "deepseek": ("deepseek", "openai_chat", False),
    "qwen": ("qwen", "openai_chat", False),
    "zhipu": ("zhipu", "openai_chat", False),
    "azure": ("custom", "openai_chat", True),
}
```

Also add `llm_migration_required` to `_BOOL_KEYS`. Call migration before inserting any missing canonical row; migration only fills absent canonical keys, then `seed_defaults()` inserts `llm_provider`, `llm_api_format`, and `llm_migration_required`. A second `seed_defaults()` call must not overwrite edited canonical values.

- [ ] **Step 4: Add shared validation and update API schemas.**

```python
def validate_provider_format(values: Mapping[str, object]) -> None:
    provider = str(values.get("llm_provider", "ollama"))
    api_format = str(values.get("llm_api_format", "ollama"))
    if api_format not in PROVIDER_FORMATS.get(provider, set()):
        raise ValueError("Unsupported provider and API format combination")
    if provider != "ollama" and not str(values.get("llm_api_key", "")).strip():
        raise ValueError("API key is required for cloud LLM providers")
```

Add `llm_provider: str = "ollama"` and `llm_api_format: str = "ollama"` to `Settings` and add the same canonical fields to `SetupRequest`; configure Setup schemas to reject Azure and unknown extra fields. Block `llm_mode` in `PUT /config`. Update Dashboard to return canonical `llm_provider`, `llm_api_format`, and `llm_migration_required`, with legacy fallback only when canonical rows are absent.
- [ ] **Step 5: Run the focused tests and the full backend suite; expected: all pass.**
- [ ] **Step 6: Commit**

```bash
git add backend/app/core/config_manager.py backend/app/schemas backend/app/api/v1 backend/app/core/settings.py backend/tests
git commit -m "feat: split llm provider and api format configuration"
```

### Task 2: Model Discovery Service and API

**Files:**
- Create: `backend/app/services/model_discovery.py`
- Modify: `backend/app/schemas/config.py`
- Modify: `backend/app/schemas/setup.py`
- Modify: `backend/app/api/v1/config.py`
- Modify: `backend/app/api/v1/setup.py`
- Test: `backend/tests/test_model_discovery.py`
- Test: `backend/tests/api/test_config.py`

**Interfaces:**
- Produce `discover_models(config: Mapping[str, object], settings: Settings) -> dict[str, object]`.
- Consume `validate_provider_format(values: Mapping[str, object]) -> None`, `resolve_base_url(config: Mapping[str, object], provider: str, settings: Settings) -> str`, and `resolve_timeout(config: Mapping[str, object], settings: Settings) -> float` from `app.core.config_manager`.
- Produce `POST /api/v1/config/models/discover` (JWT) and `POST /api/v1/setup/models/discover` (anonymous only before setup); request body is `{ "values": {...} }` and accepts unsaved provider, format, base URL, model, and API Key values.
- Return `{ok, provider, api_format, models, manual_input, category, message}` inside the standard response envelope.

- [ ] **Step 1: Write failing HTTP-mocked tests for Ollama `/api/tags`, OpenAI `/models`, Anthropic `/v1/models`, empty results, authentication errors, timeouts, and unsupported formats. Also add route tests proving Setup discovery is anonymous only before completion, returns 409 after completion, and Config discovery returns 401 without JWT.**

```python
def test_ollama_models_are_normalized(settings):
    response = httpx.Response(200, json={"models": [{"name": "qwen2.5:7b"}, {"name": "llama3.1:8b"}]})
    with patch("app.services.model_discovery.httpx.get", return_value=response):
        result = discover_models({"llm_provider": "ollama", "llm_api_format": "ollama"}, settings)
    assert result["models"] == ["qwen2.5:7b", "llama3.1:8b"]
    assert result["manual_input"] is False
```

- [ ] **Step 2: Run the focused discovery tests; verify they fail because the service and endpoint do not exist.**
- [ ] **Step 3: Implement one HTTP client boundary with configured timeout.**

```python
def discover_models(config: Mapping[str, object], settings: Settings) -> dict[str, object]:
    validate_provider_format(config)
    provider = str(config.get("llm_provider", "ollama"))
    api_format = str(config.get("llm_api_format", "ollama"))
    api_key = str(config.get("llm_api_key", ""))
    base_url = resolve_base_url(config, provider, settings).rstrip("/")
    if api_format == "ollama":
        response = httpx.get(f"{base_url}/api/tags", timeout=resolve_timeout(config, settings))
        models = [item["name"] for item in response.json().get("models", []) if item.get("name")]
    elif api_format == "anthropic_messages":
        response = httpx.get(
            f"{base_url}/v1/models",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
            timeout=resolve_timeout(config, settings),
        )
        models = [item["id"] for item in response.json().get("data", []) if item.get("id")]
    else:
        response = httpx.get(
            f"{base_url}/models",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=resolve_timeout(config, settings),
        )
        models = [item["id"] for item in response.json().get("data", []) if item.get("id")]
    return discovery_result(sorted(set(models)))
```

Catch HTTP status, timeout, transport, and parsing errors at this boundary and return only `ok`, `authentication`, `timeout`, `unreachable`, `unsupported`, or `empty` categories. Return `manual_input=True` whenever `ok` is false or the normalized list is empty.
- [ ] **Step 4: Add both routes.**

The Config route merges request values over decrypted stored values, treats `********` or an omitted/blank key as “reuse stored key,” and never logs request values. The Setup route rejects requests after `setup_completed=true`, does not read protected stored secrets, and does not persist discovery-only values. Convert service `ValueError` to the existing unified 422 response.
- [ ] **Step 5: Run discovery/API tests and the full backend suite; expected: all pass.**
- [ ] **Step 6: Commit**

```bash
git add backend/app/services/model_discovery.py backend/app/schemas/config.py backend/app/api/v1/config.py backend/tests
git commit -m "feat: add llm model discovery api"
```

### Task 3: Chat, Responses, Anthropic, and Ollama Provider Adapters

**Files:**
- Modify: `backend/requirements.txt`
- Modify: `backend/app/core/llm.py`
- Create: `backend/app/core/responses_adapter.py`
- Modify: `backend/app/services/llm_test.py`
- Test: `backend/tests/test_llm_service.py`

**Interfaces:**
- Extend `get_llm(config: Mapping[str, object], settings: Settings | None = None)` to select by `llm_api_format`.
- Produce `OpenAIResponsesAdapter` with `invoke(prompt: str) -> dict[str, object]`; streaming is out of scope for this phase.
- Add `langchain-anthropic==0.2.4`, compatible with the existing LangChain 0.3 dependency set.

- [ ] **Step 1: Write failing tests for all allowed provider/format combinations and invalid combinations.**

```python
def test_anthropic_messages_returns_chat_anthropic(monkeypatch, settings):
    monkeypatch.setattr("app.core.llm.ChatAnthropic", FakeAnthropic)
    llm = get_llm({
        "llm_provider": "anthropic",
        "llm_api_format": "anthropic_messages",
        "llm_model": "claude-sonnet-4-20250514",
        "llm_api_key": "test-key",
    }, settings)
    assert isinstance(llm, FakeAnthropic)


def test_responses_is_restricted_to_openai_or_custom(settings):
    with pytest.raises(ValueError, match="Responses"):
        get_llm({"llm_provider": "deepseek", "llm_api_format": "openai_responses", "llm_api_key": "test-key"}, settings)
```

- [ ] **Step 2: Run the focused tests; verify they fail because provider/format selection and the adapter are missing.**
- [ ] **Step 3: Implement provider adapters.**

Implement `ChatOllama` for `ollama`, `ChatOpenAI` for `openai_chat`, `ChatAnthropic` for `anthropic_messages`, and an `httpx` Responses adapter for `openai_responses`. Keep provider defaults for base URLs and model values in one mapping; import `ChatAnthropic` lazily or guard its import so existing installs fail with a clear dependency message until requirements are installed.

- [ ] **Step 4: Update the connection test.**

Update `check_llm_connection` to use the selected adapter and preserve normalized error categories. For Responses, POST to `<base_url>/responses` with model and input, parse `output_text` first and nested `output[].content[].text` as a fallback, and return safe failure messages.
- [ ] **Step 5: Run LLM service tests and the full backend suite; expected: all pass without real credentials or network.**
- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/app/core/llm.py backend/app/core/responses_adapter.py backend/app/services/llm_test.py backend/tests
git commit -m "feat: add anthropic and responses llm adapters"
```

### Task 4: Shared Frontend Provider, Format, and Model Selector

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Modify: `frontend/vitest.config.ts`
- Modify: `frontend/src/composables/llmForm.ts`
- Modify: `frontend/src/components/LlmConfigFields.vue`
- Create: `frontend/src/components/ModelSelector.vue`
- Modify: `frontend/src/api/config.ts`
- Test: `frontend/src/__tests__/llmForm.spec.ts`
- Test: `frontend/src/__tests__/ModelSelector.spec.ts`

**Interfaces:**
- Replace `LlmFormModel.llm_mode` with `llm_provider` and `llm_api_format`, retaining an optional legacy `llm_mode` only for API compatibility.
- Produce `allowedApiFormats(provider: LlmProvider): LlmApiFormat[]`.
- Produce `defaultProviderConfig(provider: LlmProvider): { api_format: LlmApiFormat; base_url: string }`.
- Produce `discoverModels(values: Record<string, unknown>, scope: "setup" | "config"): Promise<ModelDiscoveryResult>` in `frontend/src/api/config.ts`; `scope` selects the anonymous Setup or JWT Config route.
- `ModelSelector` accepts `modelValue`, `models`, `manualInput`, `loading`, `errorMessage` and emits `update:modelValue` and `discover`.

- [ ] **Step 1: Write failing Vitest tests for provider/format combinations, default URLs, Responses visibility, successful model discovery, empty discovery fallback, and discovery failure fallback. Use `@vue/test-utils` mounting for the selector so the DOM environment requirement is exercised.**
- [ ] **Step 2: Run `npm --prefix frontend run test -- --run src/__tests__/llmForm.spec.ts src/__tests__/ModelSelector.spec.ts`; verify the new exports/component behavior fails.**
- [ ] **Step 3: Implement typed provider/format constants and discovery state.**

Implement one-step provider changes that update the format and Base URL, and a model discovery state helper with states `idle`, `loading`, `ready`, and `manual`. Debounce provider/format/Base URL changes; trigger an immediate attempt on API-key blur once required fields are present.

```ts
export const PROVIDERS = ["ollama", "openai", "anthropic", "deepseek", "qwen", "zhipu", "custom"] as const;
export const FORMATS = ["ollama", "openai_chat", "openai_responses", "anthropic_messages"] as const;
export function allowedApiFormats(provider: LlmProvider): LlmApiFormat[] { return PROVIDER_FORMATS[provider]; }
export function applyProvider(model: LlmFormModel, provider: LlmProvider): LlmFormModel {
  const defaults = defaultProviderConfig(provider);
  return { ...model, llm_provider: provider, llm_api_format: defaults.api_format, llm_base_url: defaults.base_url, llm_api_key: provider === "ollama" ? "" : model.llm_api_key };
}
```

- [ ] **Step 4: Implement `ModelSelector.vue` with a refresh icon button, a select when models are available, and a text input only when discovery fails or returns an empty list. Keep manual model values accepted by the parent form.**

```vue
<el-select v-if="!manualInput && models.length" :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)"><el-option v-for="name in models" :key="name" :label="name" :value="name" /></el-select>
<el-input v-else :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" />
<el-button :loading="loading" aria-label="刷新模型" @click="$emit('discover')"><el-icon><Refresh /></el-icon></el-button>
```

- [ ] **Step 5: Update `LlmConfigFields.vue` to show provider first, constrain format options, hide API Key only for Ollama, and expose the selected model selector. Do not use whole-object `v-model` assignment with a reactive parent; emit updates and merge them in the parent.**

```ts
function updateField<K extends keyof LlmFormModel>(key: K, value: LlmFormModel[K]) {
  emit("update:modelValue", { ...props.modelValue, [key]: value });
}
function onProviderChange(provider: LlmProvider) { emit("update:modelValue", applyProvider(props.modelValue, provider)); }
```
- [ ] **Step 6: Add `happy-dom` as a pinned dev dependency and set `test.environment = "happy-dom"`; run the focused tests, full frontend tests, typecheck, and build; expected: all pass.**
- [ ] **Step 7: Commit**

```bash
git add frontend/src
git commit -m "feat: add provider format and model selector"
```

### Task 5: Setup/Settings Integration and Migration UX

**Files:**
- Modify: `frontend/src/views/Setup.vue`
- Modify: `frontend/src/views/Settings.vue`
- Modify: `frontend/src/views/Dashboard.vue`
- Modify: `frontend/src/stores/config.ts`
- Modify: `frontend/src/api/config.ts`
- Test: `frontend/src/__tests__/Setup.spec.ts`
- Test: `frontend/src/__tests__/Settings.spec.ts`

**Interfaces:**
- Setup and Settings use the same provider/format/model form contract.
- Both pages call `discoverModels` with unsaved form values and preserve existing masked secrets.
- Settings displays a migration notice and requires explicit provider, format, Base URL, and model selection when `llm_migration_required` is true.

- [ ] **Step 1: Write failing tests for Setup and Settings provider/format state, discovery refresh, migration notice, and secret preservation.**
- [ ] **Step 2: Run the focused Vitest tests; verify they fail because the views still use `llm_mode` and have no discovery state.**
- [ ] **Step 3: Update API/store types and form initialization. Load canonical config values, map legacy responses for older backends, and call the correct Setup or Config discovery route after provider/format/Base URL changes without auto-saving. Trigger API-key discovery on blur and provide manual refresh.**

```ts
const discovery = reactive<ModelDiscoveryState>({ status: "idle", models: [], errorMessage: "" });
async function discover() {
  discovery.status = "loading";
  const result = await discoverModels(form, isSetupPage ? "setup" : "config");
  discovery.models = result.models;
  discovery.status = result.manual_input ? "manual" : "ready";
  discovery.errorMessage = result.message || "";
}
```

- [ ] **Step 4: Add explicit `updateLlmForm` handlers that merge child updates into the existing reactive form. On save, omit empty API Key and Prometheus Token fields when their stored values are already set.**

```ts
function updateLlmForm(value: LlmFormModel) { Object.assign(form, value); }
let values: Record<string, unknown> = { ...form, ...alertForm };
values = omitPreservedSecret(values, "llm_api_key", secretWasSet.value);
values = omitPreservedSecret(values, "prometheus_token", prometheusTokenWasSet.value);
```

- [ ] **Step 5: Add migration UX for legacy Azure records: show the custom provider state, require a non-empty model and Base URL, and prevent selecting Azure anywhere in the UI. Update Dashboard types and labels to render canonical provider/format fields.**

```vue
<el-alert v-if="migrationRequired" type="warning" title="旧版 LLM 配置需要重新选择服务商" />
<span>{{ overview?.llm_provider }} / {{ overview?.llm_api_format }}</span>
```
- [ ] **Step 6: Run full frontend tests, typecheck, and build; expected: all pass.**
- [ ] **Step 7: Commit**

```bash
git add frontend/src
git commit -m "feat: integrate provider discovery into setup and settings"
```

### Task 6: Documentation, Compose Defaults, and End-to-End Verification

**Files:**
- Modify: `README.md`
- Modify: `.env.example`
- Create: `backend/tests/test_contracts.py`
- Create: `docs/superpowers/sdd/2026-08-29-llm-provider-format-implementation/progress.md`

**Interfaces:**
- README documents provider/format selection, model discovery fallback, Anthropic credentials, Responses restrictions, and the exact test commands.
- `.env.example` uses canonical `LLM_PROVIDER` and `LLM_API_FORMAT` defaults and contains no Azure setting.

- [ ] **Step 1: Write failing contract checks for canonical Setup defaults, both discovery endpoint envelopes, the Config JWT requirement, the post-setup Setup 409, and the absence of Azure in active UI/config metadata.**

```python
def test_discovery_envelope(client):
    response = client.post("/api/v1/setup/models/discover", json={"values": {"llm_provider": "ollama", "llm_api_format": "ollama"}})
    assert set(response.json()) == {"code", "message", "data"}


def test_active_frontend_metadata_has_no_azure():
    metadata = Path("frontend/src/composables/llmForm.ts").read_text(encoding="utf-8").lower()
    assert '"azure"' not in metadata
```

- [ ] **Step 2: Run `python3 -m pytest -q backend/tests/test_contracts.py`; record the expected failures before documentation/code cleanup.**
- [ ] **Step 3: Update README, `.env.example`, and any contract fixtures. Add migration notes explaining how legacy `llm_mode` values are mapped.**
- [ ] **Step 4: Run the complete verification matrix:**

```bash
python3 -m pytest -q backend
npm --prefix frontend run test -- --run
npm --prefix frontend run typecheck
npm --prefix frontend run build
docker compose config
docker compose --profile local config
git diff --check
```

- [ ] **Step 5: Start the stack with `docker compose up -d --build`, verify `/api/v1/health`, pre-setup `/api/v1/setup`, login, anonymous Setup discovery before setup, 409 after setup, JWT-protected Config discovery, model discovery failure fallback, and frontend HTTP 200 without real credentials.**
- [ ] **Step 6: Update the SDD progress ledger with commit SHAs and test evidence, then commit the documentation and verification changes.**

```bash
git add README.md .env.example backend/tests docs/superpowers/sdd/2026-08-29-llm-provider-format-implementation/progress.md
git commit -m "docs: verify provider format integration"
```

## Completion Criteria

- Azure is absent from provider choices, validation, defaults, and documentation.
- Existing `llm_mode` databases migrate idempotently to canonical provider/format values.
- Setup and Settings can discover models for Ollama, OpenAI-compatible, and Anthropic endpoints.
- Discovery failures and empty results expose a usable manual model input.
- Chat, Responses, Anthropic Messages, and Ollama selection follows the allowed provider/format matrix.
- API keys remain encrypted and masked, and blank secret fields preserve stored values.
- Backend and frontend tests, typecheck, build, Compose validation, and runtime smoke checks pass.
