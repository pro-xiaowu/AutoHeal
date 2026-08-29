import { ref } from "vue";
import { defineStore } from "pinia";

import { getConfig, testLlm, updateConfig, type ConfigMap } from "../api/config";

export const useConfigStore = defineStore("config", () => {
  const config = ref<ConfigMap>({});
  const loading = ref(false);

  async function loadConfig() {
    loading.value = true;
    try {
      config.value = await getConfig();
      return config.value;
    } finally {
      loading.value = false;
    }
  }

  async function saveConfig(values: Record<string, unknown>) {
    config.value = await updateConfig(values);
    return config.value;
  }

  async function testConnection(values: Record<string, unknown>) {
    return testLlm(values);
  }

  return { config, loading, loadConfig, saveConfig, testConnection };
});
