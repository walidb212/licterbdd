from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any


class OpenAIResponsesClient:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_s: int = 120,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                return json.loads(response.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc

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
            "instructions": instructions,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": user_text,
                        }
                    ],
                }
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": schema_name,
                    "schema": schema,
                    "strict": True,
                }
            },
        }
        if background:
            payload["background"] = True
        return self._request("POST", "/responses", payload)

    def retrieve_response(self, response_id: str) -> dict[str, Any]:
        return self._request("GET", f"/responses/{response_id}")

    def wait_for_response(
        self,
        response_id: str,
        *,
        poll_interval_s: float = 2.0,
        timeout_s: int = 600,
    ) -> dict[str, Any]:
        deadline = time.time() + timeout_s
        payload = self.retrieve_response(response_id)
        while payload.get("status") in {"queued", "in_progress"}:
            if time.time() >= deadline:
                raise RuntimeError(f"Timed out waiting for OpenAI background response {response_id}")
            time.sleep(poll_interval_s)
            payload = self.retrieve_response(response_id)
        return payload

    @staticmethod
    def extract_output_text(payload: dict[str, Any]) -> str:
        output_text = payload.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()

        texts: list[str] = []
        for item in payload.get("output") or []:
            if not isinstance(item, dict):
                continue
            for content in item.get("content") or []:
                if not isinstance(content, dict):
                    continue
                text_value = content.get("text") or content.get("output_text")
                if isinstance(text_value, dict):
                    text_value = text_value.get("value") or text_value.get("text") or ""
                if isinstance(text_value, str) and text_value.strip():
                    texts.append(text_value.strip())
        return "\n".join(texts).strip()
