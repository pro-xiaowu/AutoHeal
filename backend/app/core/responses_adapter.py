from collections.abc import Mapping

import httpx


class OpenAIResponsesAdapter:
    def __init__(self, *, base_url: str, api_key: str, model: str, timeout: float = 60):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def invoke(self, prompt: str) -> dict[str, object]:
        response = httpx.post(
            f"{self.base_url}/responses",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json={"model": self.model, "input": prompt},
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            response.raise_for_status()
        payload = response.json()
        text = payload.get("output_text")
        if not text:
            parts: list[str] = []
            for item in payload.get("output", []):
                if not isinstance(item, Mapping):
                    continue
                for content in item.get("content", []):
                    if isinstance(content, Mapping) and content.get("text"):
                        parts.append(str(content["text"]))
            text = "".join(parts)
        if not text:
            raise ValueError("Responses API returned no text")
        return {"content": str(text), "raw": payload}
