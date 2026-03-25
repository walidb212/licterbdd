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
        # Mistral handles json_object better than strict json_schema.
        # Embed the schema description in the system prompt instead.
        enhanced_instructions = (
            instructions + "\n\n"
            "CRITICAL: Return valid JSON with this exact structure:\n"
            '{"items": [{"item_key": "<EXACT item_key from input>", "language": "fr|en", '
            '"sentiment_label": "positive|neutral|negative|mixed", "sentiment_confidence": 0.0-1.0, '
            '"themes": ["snake_case_theme", ...], "risk_flags": ["snake_case_flag", ...], '
            '"opportunity_flags": ["snake_case_flag", ...], "priority_score": 0-100, '
            '"summary_short": "max 220 chars", "evidence_spans": ["quote1", "quote2"]}]}\n\n'
            "IMPORTANT: You MUST return one item per input item. "
            "Copy the item_key EXACTLY as provided — do NOT modify, truncate or paraphrase it.\n"
            "Use these standard themes when applicable: "
            "service_client, retour_remboursement, qualite_produit, livraison_stock, "
            "magasin_experience, prix_promo, velo_mobilite, brand_controversy, "
            "community_engagement, sponsoring_partnership, running_fitness, football_teamwear.\n"
        )
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": enhanced_instructions},
                {"role": "user", "content": user_text},
            ],
            "response_format": {"type": "json_object"},
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
