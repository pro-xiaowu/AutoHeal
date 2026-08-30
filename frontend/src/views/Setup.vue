<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";

import { completeSetup, discoverModels, type SetupPayload, type ModelDiscoveryResult } from "../api/config";
import LlmConfigFields from "../components/LlmConfigFields.vue";
import { mergeLlmForm, type LlmFormModel } from "../composables/llmForm";

const router = useRouter();
const submitting = ref(false);
const form = reactive<SetupPayload>({
  username: "admin",
  password: "",
  llm_provider: "ollama",
  llm_api_format: "ollama",
  llm_model: "qwen2.5:7b",
  llm_base_url: "http://ollama:11434",
  llm_api_key: "",
  llm_temperature: 0.1,
  llm_max_tokens: 2048,
  llm_timeout: 60,
  llm_max_retries: 3,
  prometheus_url: "",
  prometheus_token: "",
});
const llmFields = ref<InstanceType<typeof LlmConfigFields>>();
const discovery = reactive({ models: [] as string[], loading: false, manual: true, error: "" });

function updateLlmForm(value: LlmFormModel) {
  mergeLlmForm(form, value);
  void discover();
}

async function discover() {
  const ready = form.llm_provider === "ollama" || Boolean(form.llm_api_key.trim());
  if (!ready || !form.llm_base_url.trim()) return;
  discovery.loading = true;
  try {
    const result: ModelDiscoveryResult = await discoverModels(form, "setup");
    discovery.models = result.models;
    discovery.manual = result.manual_input;
    discovery.error = result.message || "";
  } catch (error) {
    discovery.manual = true;
    discovery.error = error instanceof Error ? error.message : "模型获取失败";
  } finally { discovery.loading = false; }
}

async function submit() {
  if (!form.username.trim() || form.password.length < 8) {
    ElMessage.warning("管理员账号和至少 8 位密码为必填项");
    return;
  }
  if (!llmFields.value?.validateApiKey()) return;
  submitting.value = true;
  try {
    await completeSetup(form);
    ElMessage.success("初始化完成，请登录控制台");
    router.push("/login");
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : "初始化失败");
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <main class="setup-page">
    <div class="setup-orbit" aria-hidden="true"><span></span><span></span><span></span></div>
    <div class="setup-container">
      <header class="setup-header"><div class="brand-lockup"><div class="brand-mark"><span></span><span></span><span></span></div><div><strong>AutoHeal</strong><small>FIRST BOOT / SETUP</small></div></div><span class="step-count">01 <i>/</i> 01</span></header>
      <div class="setup-heading"><span class="eyebrow">INITIALIZE CONTROL PLANE</span><h1>把运行环境<br /><em>接入进来。</em></h1><p>完成一次配置，之后所有运维动作都从这里开始。</p></div>
      <el-form class="setup-form" label-position="top" @submit.prevent="submit">
        <section class="form-section"><div class="section-kicker">01 / ADMINISTRATOR</div><div class="field-grid"><el-form-item label="管理员账号"><el-input v-model="form.username" placeholder="admin" /></el-form-item><el-form-item label="登录密码"><el-input v-model="form.password" type="password" show-password placeholder="至少 8 位字符" /></el-form-item></div></section>
        <section class="form-section"><div class="section-kicker">02 / AI ENGINE</div><LlmConfigFields ref="llmFields" :model-value="form" :models="discovery.models" :model-loading="discovery.loading" :manual-model-input="discovery.manual" :model-error="discovery.error" @update:model-value="updateLlmForm" @discover="discover" /></section>
        <section class="form-section"><div class="section-kicker">03 / ALERT SOURCE</div><div class="field-grid"><el-form-item label="Prometheus 地址"><el-input v-model="form.prometheus_url" placeholder="可稍后在设置中添加" /></el-form-item><el-form-item label="访问 Token"><el-input v-model="form.prometheus_token" type="password" show-password placeholder="可选" /></el-form-item></div></section>
        <div class="setup-submit"><div><span class="status-dot"></span>配置可在初始化后随时修改</div><button class="primary-action" type="submit" :disabled="submitting"><span>{{ submitting ? "正在保存" : "完成初始化" }}</span><span aria-hidden="true">↗</span></button></div>
      </el-form>
    </div>
  </main>
</template>
