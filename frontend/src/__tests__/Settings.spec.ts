import { describe, expect, it } from "vitest";

import { apiKeyError, defaultBaseUrl, isCloudMode } from "../composables/llmForm";

describe("Settings page LLM validation contract", () => {
  it("hides the key requirement in local mode and enables it for cloud mode", () => {
    expect(isCloudMode("local")).toBe(false);
    expect(isCloudMode("openai")).toBe(true);
    expect(apiKeyError("local", "")).toBeUndefined();
    expect(apiKeyError("openai", "")).toBeTruthy();
  });

  it("uses a mode-specific base URL when the mode changes", () => {
    expect(defaultBaseUrl("deepseek")).toBe("https://api.deepseek.com/v1");
    expect(defaultBaseUrl("zhipu")).toContain("bigmodel.cn");
  });
});
