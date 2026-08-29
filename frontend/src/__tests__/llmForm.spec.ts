import { describe, expect, it } from "vitest";

import { apiKeyError, applyLlmMode, defaultBaseUrl, isCloudMode, mergeLlmForm, omitPreservedSecret } from "../composables/llmForm";

describe("LLM form mode rules", () => {
  it("treats local mode as not requiring an API key", () => {
    expect(isCloudMode("local")).toBe(false);
    expect(apiKeyError("local", "")).toBeUndefined();
  });

  it("requires an API key for cloud modes", () => {
    expect(isCloudMode("openai")).toBe(true);
    expect(apiKeyError("openai", "")).toBe("云端模式需要填写 API Key");
    expect(apiKeyError("deepseek", "sk-test")).toBeUndefined();
  });

  it("returns provider defaults for the selected mode", () => {
    expect(defaultBaseUrl("local")).toBe("http://ollama:11434");
    expect(defaultBaseUrl("qwen")).toContain("dashscope.aliyuncs.com");
  });

  it("updates mode and dependent fields in one state transition", () => {
    const next = applyLlmMode(
      { llm_mode: "local", llm_base_url: "http://ollama:11434", llm_api_key: "" },
      "deepseek",
    );

    expect(next).toEqual({
      llm_mode: "deepseek",
      llm_base_url: "https://api.deepseek.com/v1",
      llm_api_key: "",
    });
  });

  it("omits an unchanged secret instead of clearing it", () => {
    expect(omitPreservedSecret({ prometheus_token: "" }, "prometheus_token", true)).toEqual({});
    expect(omitPreservedSecret({ prometheus_token: "new-secret" }, "prometheus_token", true)).toEqual({ prometheus_token: "new-secret" });
  });

  it("merges child updates into the existing form object", () => {
    const current = { llm_mode: "local", llm_base_url: "http://ollama:11434", llm_api_key: "" };
    mergeLlmForm(current, { llm_mode: "qwen", llm_base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1" });
    expect(current).toEqual({ llm_mode: "qwen", llm_base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1", llm_api_key: "" });
  });
});
