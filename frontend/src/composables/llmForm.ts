export const LLM_PROVIDERS = ["ollama", "openai", "anthropic", "deepseek", "qwen", "zhipu", "custom"] as const;
export type LlmProvider = (typeof LLM_PROVIDERS)[number];
export const LLM_MODES = ["local", "openai", "deepseek", "qwen", "zhipu"] as const;
export type LlmMode = (typeof LLM_MODES)[number];
export const LLM_API_FORMATS = ["ollama", "openai_chat", "openai_responses", "anthropic_messages"] as const;
export type LlmApiFormat = (typeof LLM_API_FORMATS)[number];
export const PROVIDER_FORMATS: Record<LlmProvider, LlmApiFormat[]> = {
  ollama: ["ollama"], openai: ["openai_chat", "openai_responses"], anthropic: ["anthropic_messages"],
  deepseek: ["openai_chat"], qwen: ["openai_chat"], zhipu: ["openai_chat"], custom: ["openai_chat", "openai_responses", "anthropic_messages"],
};
export const DEFAULT_BASE_URLS: Record<LlmProvider, string> = {
  ollama: "http://ollama:11434", openai: "https://api.openai.com/v1", anthropic: "https://api.anthropic.com",
  deepseek: "https://api.deepseek.com/v1", qwen: "https://dashscope.aliyuncs.com/compatible-mode/v1", zhipu: "https://open.bigmodel.cn/api/paas/v4", custom: "",
};
export interface LlmFormModel { llm_provider: LlmProvider; llm_api_format: LlmApiFormat; llm_model: string; llm_base_url: string; llm_api_key: string; llm_temperature: number; llm_max_tokens: number; llm_timeout: number; llm_max_retries: number; llm_mode?: string; }
export function allowedApiFormats(provider: LlmProvider): LlmApiFormat[] { return PROVIDER_FORMATS[provider]; }
export function defaultProviderConfig(provider: LlmProvider): { api_format: LlmApiFormat; base_url: string } { return { api_format: PROVIDER_FORMATS[provider][0], base_url: DEFAULT_BASE_URLS[provider] }; }
export function defaultBaseUrl(provider: LlmProvider | LlmMode): string { return DEFAULT_BASE_URLS[provider === "local" ? "ollama" : provider]; }
export function isCloudProvider(provider: LlmProvider): boolean { return provider !== "ollama"; }
export function isCloudMode(provider: LlmProvider | LlmMode): boolean { return provider !== "ollama" && provider !== "local"; }
export function apiKeyError(provider: LlmProvider | LlmMode, apiKey: string): string | undefined { return isCloudMode(provider) && !apiKey.trim() ? "云端模式需要填写 API Key" : undefined; }
export function applyProvider<T extends { llm_provider: LlmProvider; llm_api_format: LlmApiFormat; llm_base_url: string; llm_api_key: string }>(model: T, provider: LlmProvider): T { const defaults = defaultProviderConfig(provider); return { ...model, llm_provider: provider, llm_api_format: defaults.api_format, llm_base_url: defaults.base_url, llm_api_key: provider === "ollama" ? "" : model.llm_api_key }; }
export function applyLlmMode<T extends { llm_mode: LlmMode; llm_base_url: string; llm_api_key: string }>(model: T, mode: LlmMode): T { return { ...model, llm_mode: mode, llm_base_url: defaultBaseUrl(mode), llm_api_key: mode === "local" ? "" : model.llm_api_key }; }
export function omitPreservedSecret<T extends Record<string, unknown>>(values: T, key: string, wasSet: boolean): T { if (!wasSet || (values[key] && values[key] !== "********")) return values; const next = { ...values }; delete next[key]; return next; }
export function mergeLlmForm<T extends object>(target: T, source: Partial<T>): T { Object.assign(target, source); return target; }
