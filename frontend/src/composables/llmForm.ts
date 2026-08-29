export const LLM_MODES = ["local", "openai", "deepseek", "qwen", "azure", "zhipu"] as const;

export type LlmMode = (typeof LLM_MODES)[number];

export const CLOUD_MODES = new Set<LlmMode>(["openai", "deepseek", "qwen", "azure", "zhipu"]);

export const DEFAULT_BASE_URLS: Record<LlmMode, string> = {
  local: "http://ollama:11434",
  openai: "https://api.openai.com/v1",
  deepseek: "https://api.deepseek.com/v1",
  qwen: "https://dashscope.aliyuncs.com/compatible-mode/v1",
  azure: "https://api.openai.com/v1",
  zhipu: "https://open.bigmodel.cn/api/paas/v4",
};

export function isCloudMode(mode: LlmMode): boolean {
  return CLOUD_MODES.has(mode);
}

export function defaultBaseUrl(mode: LlmMode): string {
  return DEFAULT_BASE_URLS[mode];
}

export function apiKeyError(mode: LlmMode, apiKey: string): string | undefined {
  if (isCloudMode(mode) && !apiKey.trim()) return "云端模式需要填写 API Key";
  return undefined;
}

export function applyLlmMode<T extends { llm_mode: LlmMode; llm_base_url: string; llm_api_key: string }>(model: T, mode: LlmMode): T {
  return {
    ...model,
    llm_mode: mode,
    llm_base_url: defaultBaseUrl(mode),
    llm_api_key: isCloudMode(mode) ? model.llm_api_key : "",
  };
}

export function omitPreservedSecret<T extends Record<string, unknown>>(values: T, key: string, wasSet: boolean): T {
  if (!wasSet || values[key]) return values;
  const next = { ...values };
  delete next[key];
  return next;
}

export function mergeLlmForm<T extends object>(target: T, source: Partial<T>): T {
  Object.assign(target, source);
  return target;
}
