<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { ElMessage } from "element-plus";

import LlmConfigFields, { type LlmFormModel } from "../components/LlmConfigFields.vue";
import { useConfigStore } from "../stores/config";
import { mergeLlmForm, omitPreservedSecret } from "../composables/llmForm";

const store = useConfigStore();
const loading = ref(true);
const saving = ref(false);
const testing = ref(false);
const secretWasSet = ref(false);
const prometheusTokenWasSet = ref(false);
const llmFields = ref<InstanceType<typeof LlmConfigFields>>();
const form = reactive<LlmFormModel>({
  llm_mode: "local", llm_model: "qwen2.5:7b", llm_base_url: "http://ollama:11434", llm_api_key: "",
  llm_temperature: 0.1, llm_max_tokens: 2048, llm_timeout: 60, llm_max_retries: 3,
});
const alertForm = reactive({ prometheus_url: "", prometheus_token: "" });

function updateLlmForm(value: LlmFormModel) {
  mergeLlmForm(form, value);
}

const stateLabel = computed(() => form.llm_mode === "local" ? "LOCAL RUNTIME" : "CLOUD RUNTIME");

function applyConfig(config: Record<string, { value: string | number | boolean; is_set: boolean }>) {
  for (const key of Object.keys(form) as Array<keyof LlmFormModel>) {
    const entry = config[key];
    if (entry) (form[key] as string | number) = entry.value as never;
  }
  const apiEntry = config.llm_api_key;
  secretWasSet.value = Boolean(apiEntry?.is_set);
  if (apiEntry?.is_set) form.llm_api_key = "";
  prometheusTokenWasSet.value = Boolean(config.prometheus_token?.is_set);
  alertForm.prometheus_url = String(config.prometheus_url?.value || "");
  alertForm.prometheus_token = "";
}

async function load() {
  loading.value = true;
  try { applyConfig(await store.loadConfig()); } catch (error) { ElMessage.error(error instanceof Error ? error.message : "配置读取失败"); } finally { loading.value = false; }
}

async function save() {
  if (!llmFields.value?.validateApiKey()) return;
  saving.value = true;
  try {
    let values: Record<string, unknown> = { ...form, ...alertForm };
    values = omitPreservedSecret(values, "llm_api_key", secretWasSet.value);
    values = omitPreservedSecret(values, "prometheus_token", prometheusTokenWasSet.value);
    const config = await store.saveConfig(values);
    applyConfig(config);
    ElMessage.success("配置已保存并即时生效");
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : "保存失败"); } finally { saving.value = false; }
}

async function testConnection() {
  if (!llmFields.value?.validateApiKey()) return;
  testing.value = true;
  try {
    const values: Record<string, unknown> = { ...form };
    if (!form.llm_api_key && secretWasSet.value) delete values.llm_api_key;
    const result = await store.testConnection(values);
    if (result.ok) ElMessage.success(`${result.message} · ${result.latency_ms}ms`);
    else ElMessage.error(result.message);
  } catch (error) { ElMessage.error(error instanceof Error ? error.message : "连接测试失败"); } finally { testing.value = false; }
}

onMounted(load);
</script>

<template>
  <div v-loading="loading" class="settings-view">
    <div class="view-intro"><div><span class="eyebrow">CONTROL PLANE / RUNTIME</span><h2>系统设置</h2><p>配置会即时生效，敏感凭据仅在服务端加密保存。</p></div><div class="runtime-badge"><span class="status-dot"></span>{{ stateLabel }}</div></div>
    <el-form label-position="top" class="settings-form">
      <section class="settings-section"><div class="section-heading"><div><span class="section-index">01</span><h3>AI 引擎</h3></div><button class="ghost-action" type="button" :disabled="testing" @click="testConnection"><span class="pulse-icon"></span>{{ testing ? "测试中" : "测试连接" }}</button></div><LlmConfigFields ref="llmFields" :model-value="form" @update:model-value="updateLlmForm" /></section>
      <section class="settings-section"><div class="section-heading"><div><span class="section-index">02</span><h3>告警源</h3></div><span class="section-state">OPTIONAL</span></div><div class="field-grid"><el-form-item label="Prometheus 地址"><el-input v-model="alertForm.prometheus_url" placeholder="http://prometheus:9090" /></el-form-item><el-form-item label="访问 Token"><el-input v-model="alertForm.prometheus_token" type="password" show-password placeholder="留空表示不修改" /></el-form-item></div></section>
      <section class="settings-section"><div class="section-heading"><div><span class="section-index">03</span><h3>运行状态</h3></div></div><div class="status-table"><div><span>配置存储</span><b>SQLite / encrypted</b><i class="ok-text">READY</i></div><div><span>会话缓存</span><b>Redis 7</b><i class="muted-text">PENDING</i></div><div><span>知识库</span><b>ChromaDB</b><i class="muted-text">PENDING</i></div></div></section>
      <div class="form-actions"><span><span class="status-dot"></span>未保存的变更仅存在于当前页面</span><button class="primary-action" type="button" :disabled="saving || loading" @click="save"><span>{{ saving ? "保存中" : "保存配置" }}</span><span aria-hidden="true">↗</span></button></div>
    </el-form>
  </div>
</template>
