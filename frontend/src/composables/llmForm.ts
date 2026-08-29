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
