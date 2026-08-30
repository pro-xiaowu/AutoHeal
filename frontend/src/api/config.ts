import http from "./http";
import type { LlmApiFormat, LlmProvider } from "../composables/llmForm";

export interface SetupPayload {
  username: string;
  password: string;
  llm_provider: LlmProvider;
  llm_api_format: LlmApiFormat;
  llm_model: string;
  llm_base_url: string;
  llm_api_key: string;
  llm_temperature: number;
  llm_max_tokens: number;
  llm_timeout: number;
  llm_max_retries: number;
  prometheus_url: string;
  prometheus_token: string;
}

export interface ModelDiscoveryResult {
  ok: boolean;
  provider: string;
  api_format: string;
  models: string[];
  manual_input: boolean;
  category: string;
  message: string;
}

export interface ConfigEntry {
  value: string | number | boolean;
  is_set: boolean;
  is_secret: boolean;
  category: string;
  description: string;
}

export type ConfigMap = Record<string, ConfigEntry>;

export async function getSetupStatus() {
  const response = await http.get("/setup");
  return response.data.data;
}

export async function completeSetup(payload: SetupPayload) {
  const response = await http.post("/setup", payload);
  return response.data.data;
}

export async function getConfig(): Promise<ConfigMap> {
  const response = await http.get("/config");
  return response.data.data;
}

export async function updateConfig(values: Record<string, unknown>): Promise<ConfigMap> {
  const response = await http.put("/config", { values });
  return response.data.data;
}

export async function testLlm(values: Record<string, unknown>) {
  const response = await http.post("/config/test/llm", { values });
  return response.data.data;
}

export async function discoverModels(values: Record<string, unknown>, scope: "setup" | "config" = "config"): Promise<ModelDiscoveryResult> {
  const response = await http.post(scope === "setup" ? "/setup/models/discover" : "/config/models/discover", { values });
  return response.data.data;
}

export async function getDashboardOverview() {
  const response = await http.get("/dashboard/overview");
  return response.data.data;
}
