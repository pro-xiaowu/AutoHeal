<script setup lang="ts">
import { Refresh } from "@element-plus/icons-vue";
defineProps<{ modelValue: string; models: string[]; manualInput: boolean; loading: boolean; errorMessage: string }>();
defineEmits<{ "update:modelValue": [value: string]; discover: [] }>();
</script>
<template><div class="model-selector"><el-select v-if="!manualInput && models.length" :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)"><el-option v-for="name in models" :key="name" :label="name" :value="name" /></el-select><el-input v-else :model-value="modelValue" placeholder="手动输入模型名称" @update:model-value="$emit('update:modelValue', $event)" /><el-button class="model-refresh" :loading="loading" aria-label="刷新模型" title="刷新模型" @click="$emit('discover')"><el-icon><Refresh /></el-icon></el-button><small v-if="errorMessage" class="model-error">{{ errorMessage }}</small></div></template>
<style scoped>.model-selector { display: flex; gap: 8px; position: relative; width: 100%; }.model-selector > .el-select, .model-selector > .el-input { flex: 1; }.model-refresh { width: 40px; min-height: 32px; padding: 0; }.model-error { position: absolute; top: calc(100% + 4px); color: var(--amber); font-size: 11px; }</style>
