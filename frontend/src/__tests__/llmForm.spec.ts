import { describe, expect, it } from "vitest";

import { apiKeyError, defaultBaseUrl, isCloudMode } from "../composables/llmForm";

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
});
