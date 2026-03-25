from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class MistralChatClient:
    """HTTP client for Mistral Chat Completions API (OpenAI-compatible).

    Interface is compatible with OpenRouterChatClient / OpenAIResponsesClient
    so that _enrich_with_openai() can consume it via duck typing.
    """

    _BASE_URL = "https://api.mistral.ai/v1"

    def __init__(
        self,
        *,
        api_key: str,
        model: str = "mistral-small-latest",
        timeout_s: int = 120,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self._BASE_URL}/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                return json.loads(response.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"Mistral HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Mistral request failed: {exc}") from exc

    def create_structured_response(
        self,
        *,
        instructions: str,
        user_text: str,
        schema_name: str,
        schema: dict[str, Any],
        background: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": user_text},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                },
            },
        }
        raw = self._request(payload)
        content = (
            (raw.get("choices") or [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        return {"output_text": content, "status": "completed"}

    @staticmethod
    def extract_output_text(payload: dict[str, Any]) -> str:
        output_text = payload.get("output_text", "")
        if isinstance(output_text, str):
            return output_text.strip()
        return ""
