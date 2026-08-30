<script setup lang="ts">
import { computed } from "vue";
import { ElMessage } from "element-plus";
import ModelSelector from "./ModelSelector.vue";
import { allowedApiFormats, apiKeyError, applyProvider, isCloudProvider, LLM_PROVIDERS, type LlmApiFormat, type LlmFormModel, type LlmProvider } from "../composables/llmForm";
export type { LlmFormModel } from "../composables/llmForm";
const props = withDefaults(defineProps<{ modelValue: LlmFormModel; models?: string[]; modelLoading?: boolean; manualModelInput?: boolean; modelError?: string }>(), { models: () => [], modelLoading: false, manualModelInput: true, modelError: "" });
const emit = defineEmits<{ "update:modelValue": [value: LlmFormModel]; discover: [] }>();
const model = computed(() => props.modelValue);
const cloudMode = computed(() => isCloudProvider(model.value.llm_provider));
const providerLabels: Record<LlmProvider, string> = { ollama: "Ollama 本地", openai: "OpenAI", anthropic: "Anthropic", deepseek: "DeepSeek", qwen: "通义千问", zhipu: "智谱 AI", custom: "自定义网关" };
const formatLabels: Record<LlmApiFormat, string> = { ollama: "Ollama API", openai_chat: "OpenAI Chat", openai_responses: "OpenAI Responses", anthropic_messages: "Anthropic Messages" };
function updateField<K extends keyof LlmFormModel>(key: K, value: LlmFormModel[K]) { emit("update:modelValue", { ...model.value, [key]: value }); }
function changeProvider(provider: LlmProvider) { emit("update:modelValue", applyProvider(model.value, provider)); }
function validateApiKey() { const message = apiKeyError(model.value.llm_provider, model.value.llm_api_key); if (message) ElMessage.warning(message); return !message; }
defineExpose({ validateApiKey, cloudMode });
</script>
<template>
  <div class="llm-fields">
    <div class="field-grid">
      <el-form-item label="服务商" prop="llm_provider"><el-select :model-value="model.llm_provider" @update:model-value="changeProvider"><el-option v-for="provider in LLM_PROVIDERS" :key="provider" :label="providerLabels[provider]" :value="provider" /></el-select></el-form-item>
      <el-form-item label="API 格式" prop="llm_api_format"><el-select :model-value="model.llm_api_format" @update:model-value="updateField('llm_api_format', $event)"><el-option v-for="format in allowedApiFormats(model.llm_provider)" :key="format" :label="formatLabels[format]" :value="format" /></el-select></el-form-item>
    </div>
    <el-form-item label="模型名称" prop="llm_model"><ModelSelector :model-value="model.llm_model" :models="props.models" :manual-input="props.manualModelInput" :loading="props.modelLoading" :error-message="props.modelError" @update:model-value="updateField('llm_model', $event)" @discover="emit('discover')" /></el-form-item>
    <el-form-item label="服务地址" prop="llm_base_url"><el-input :model-value="model.llm_base_url" @update:model-value="updateField('llm_base_url', $event)" /></el-form-item>
    <el-form-item v-if="cloudMode" label="API Key" prop="llm_api_key"><el-input :model-value="model.llm_api_key" type="password" show-password autocomplete="new-password" placeholder="输入服务密钥" @update:model-value="updateField('llm_api_key', $event)" @blur="emit('discover')" /></el-form-item>
    <div v-else class="inline-note"><span class="status-dot"></span>本地模式无需 API Key，数据留在你的网络内。</div>
    <div class="field-grid compact"><el-form-item label="Temperature"><el-slider :model-value="model.llm_temperature" :min="0" :max="1" :step="0.05" @update:model-value="updateField('llm_temperature', $event as number)" /><span class="slider-value">{{ model.llm_temperature.toFixed(2) }}</span></el-form-item><el-form-item label="最大输出 Token"><el-input-number :model-value="model.llm_max_tokens" :min="1" :max="200000" controls-position="right" @update:model-value="updateField('llm_max_tokens', $event || 1)" /></el-form-item><el-form-item label="超时（秒）"><el-input-number :model-value="model.llm_timeout" :min="1" :max="3600" controls-position="right" @update:model-value="updateField('llm_timeout', $event || 1)" /></el-form-item><el-form-item label="失败重试"><el-input-number :model-value="model.llm_max_retries" :min="0" :max="20" controls-position="right" @update:model-value="updateField('llm_max_retries', $event || 0)" /></el-form-item></div>
  </div>
</template>
