<script setup lang="ts">
import { computed } from "vue";
import { ElMessage } from "element-plus";

import {
  LLM_MODES,
  apiKeyError,
  isCloudMode,
  applyLlmMode,
  type LlmMode,
} from "../composables/llmForm";

export interface LlmFormModel {
  llm_mode: LlmMode;
  llm_model: string;
  llm_base_url: string;
  llm_api_key: string;
  llm_temperature: number;
  llm_max_tokens: number;
  llm_timeout: number;
  llm_max_retries: number;
}

const props = defineProps<{ modelValue: LlmFormModel }>();
const emit = defineEmits<{ "update:modelValue": [value: LlmFormModel] }>();

const model = computed(() => props.modelValue);
const cloudMode = computed(() => isCloudMode(model.value.llm_mode));
const modeLabels: Record<LlmMode, string> = {
  local: "Ollama 本地",
  openai: "OpenAI",
  deepseek: "DeepSeek",
  qwen: "通义千问",
  azure: "Azure OpenAI",
  zhipu: "智谱 AI",
};

function updateField<K extends keyof LlmFormModel>(key: K, value: LlmFormModel[K]) {
  emit("update:modelValue", { ...model.value, [key]: value });
}

function changeMode(mode: LlmMode) {
  emit("update:modelValue", applyLlmMode(model.value, mode));
}

function validateApiKey() {
  const message = apiKeyError(model.value.llm_mode, model.value.llm_api_key);
  if (message) ElMessage.warning(message);
  return !message;
}

defineExpose({ validateApiKey, cloudMode });
</script>

<template>
  <div class="llm-fields">
    <div class="field-grid">
      <el-form-item label="调用模式" prop="llm_mode">
        <el-select :model-value="model.llm_mode" @update:model-value="changeMode">
          <el-option v-for="mode in LLM_MODES" :key="mode" :label="modeLabels[mode]" :value="mode" />
        </el-select>
      </el-form-item>
      <el-form-item label="模型名称" prop="llm_model">
        <el-input :model-value="model.llm_model" placeholder="例如 qwen2.5:7b" @update:model-value="updateField('llm_model', $event)" />
      </el-form-item>
    </div>

    <el-form-item label="服务地址" prop="llm_base_url">
      <el-input :model-value="model.llm_base_url" @update:model-value="updateField('llm_base_url', $event)" />
    </el-form-item>

    <el-form-item v-if="cloudMode" label="API Key" prop="llm_api_key">
      <el-input
        :model-value="model.llm_api_key"
        type="password"
        show-password
        autocomplete="new-password"
        placeholder="输入后端服务密钥"
        @update:model-value="updateField('llm_api_key', $event)"
      />
    </el-form-item>
    <div v-else class="inline-note"><span class="status-dot"></span>本地模式无需 API Key，数据留在你的网络内。</div>

    <div class="field-grid compact">
      <el-form-item label="Temperature">
        <el-slider :model-value="model.llm_temperature" :min="0" :max="1" :step="0.05" @update:model-value="updateField('llm_temperature', $event as number)" />
        <span class="slider-value">{{ model.llm_temperature.toFixed(2) }}</span>
      </el-form-item>
      <el-form-item label="最大输出 Token">
        <el-input-number :model-value="model.llm_max_tokens" :min="1" :max="200000" controls-position="right" @update:model-value="updateField('llm_max_tokens', $event || 1)" />
      </el-form-item>
      <el-form-item label="超时（秒）">
        <el-input-number :model-value="model.llm_timeout" :min="1" :max="3600" controls-position="right" @update:model-value="updateField('llm_timeout', $event || 1)" />
      </el-form-item>
      <el-form-item label="失败重试">
        <el-input-number :model-value="model.llm_max_retries" :min="0" :max="20" controls-position="right" @update:model-value="updateField('llm_max_retries', $event || 0)" />
      </el-form-item>
    </div>
  </div>
</template>
