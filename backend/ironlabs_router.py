"""
IronLabsRouter — working stub for the ML branch.

The backend PR (P1) will expand this with:
  - DB logging to ironlabs_calls table
  - CSV logging to data/ironlabs_log.csv
  - Cost tracking per token
  - Richer fallback error reporting

This stub makes real HTTP calls and handles fallbacks.
"""

import os
from typing import Optional

import httpx

IRONLABS_API_KEY = os.getenv("IRONLABS_API_KEY", "")
IRONLABS_BASE_URL = os.getenv("IRONLABS_BASE_URL", "https://api.ironlabs.ai/v1")

# Architecture PRD §8 routing matrix
_FALLBACK_CHAINS: dict[str, list[str]] = {
    "forensics_vision":   ["gpt-4o-mini", "claude-haiku-20240307"],
    "clinical_vision":    ["claude-haiku-20240307", "gpt-4o-mini"],
    "critical_decision":  ["claude-sonnet-20241022", "gpt-4o-mini", "llama-3.1-8b-instruct"],
    "metadata_extraction": ["llama-3.1-8b-instruct", "gpt-4o-mini"],
    "audit_format":       ["llama-3.1-8b-instruct", "gpt-4o-mini"],
}

_STATIC_FALLBACK = "ESCALATE: all IronLabs models unavailable"


class IronLabsRouter:
    def __init__(self) -> None:
        self._base = IRONLABS_BASE_URL.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {IRONLABS_API_KEY}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def route(self, task_type: str, prompt: str) -> str:
        """Text-only call. Returns the model's reply as a string."""
        for model in _FALLBACK_CHAINS.get(task_type, ["llama-3.1-8b-instruct"]):
            result = await self._call_text(model, prompt)
            if result is not None:
                return result
        return _STATIC_FALLBACK

    async def route_vision(self, task_type: str, prompt: str, image_b64: str) -> str:
        """Vision call (image + text). Returns the model's reply as a string."""
        for model in _FALLBACK_CHAINS.get(task_type, ["gpt-4o-mini"]):
            result = await self._call_vision(model, prompt, image_b64)
            if result is not None:
                return result
        return '{"error": "all_models_unavailable"}'

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _call_text(self, model: str, prompt: str) -> Optional[str]:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
        }
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                r = await client.post(
                    f"{self._base}/chat/completions",
                    headers=self._headers,
                    json=payload,
                )
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except Exception:
            return None

    async def _call_vision(self, model: str, prompt: str, image_b64: str) -> Optional[str]:
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                        },
                    ],
                }
            ],
            "max_tokens": 1024,
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                r = await client.post(
                    f"{self._base}/chat/completions",
                    headers=self._headers,
                    json=payload,
                )
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except Exception:
            return None
