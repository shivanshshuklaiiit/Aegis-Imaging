import os
import csv
import time
import datetime
import logging
from pathlib import Path

from openai import AsyncOpenAI
from db import log_ironlabs_call

logger = logging.getLogger(__name__)

IRONLABS_API_KEY = os.getenv("IRONLABS_API_KEY", "")
IRONLABS_BASE_URL = os.getenv("IRONLABS_BASE_URL", "https://api.ironlabs.ai/v1")
LOG_CSV_PATH = Path("data/ironlabs_log.csv")

MODELS = {
    "cheap": os.getenv("IRONLABS_MODEL_CHEAP", "llama-3.1-8b-instruct"),
    "mid":   os.getenv("IRONLABS_MODEL_MID",   "gpt-4o-mini"),
    "top":   os.getenv("IRONLABS_MODEL_TOP",   "claude-sonnet-4-5"),
}

# USD per 1K tokens (blended input+output estimate)
COST_PER_1K = {"cheap": 0.0002, "mid": 0.0015, "top": 0.015}

# Maps task_type → starting model tier
TASK_ROUTING: dict[str, str] = {
    "metadata_extraction": "cheap",
    "vision_forensics":    "mid",
    "clinical_analysis":   "mid",
    "critical_decision":   "top",
    "audit_format":        "cheap",
}

# Fallback order: if a tier fails, try the next one down
FALLBACK_ORDER = ["top", "mid", "cheap"]

STATIC_FALLBACK = (
    "Automated rationale unavailable — all model tiers failed. "
    "Manual clinical review is required."
)


class IronLabsRouter:
    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=IRONLABS_API_KEY or "placeholder",
            base_url=IRONLABS_BASE_URL,
        )
        LOG_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not LOG_CSV_PATH.exists():
            with open(LOG_CSV_PATH, "w", newline="") as f:
                csv.writer(f).writerow(
                    ["timestamp", "audit_id", "agent", "model", "task_type",
                     "tokens", "cost_usd", "latency_ms", "error"]
                )
        if not IRONLABS_API_KEY:
            logger.warning("IRONLABS_API_KEY not set — LLM calls will fail and return static fallback")

    async def route(
        self,
        task_type: str,
        prompt: str,
        image_b64: str | None = None,
        audit_id: str | None = None,
        agent: str | None = None,
        max_tokens: int = 512,
    ) -> str:
        start_tier = TASK_ROUTING.get(task_type, "mid")
        tiers = self._fallback_chain(start_tier)

        for tier in tiers:
            result = await self._call(
                tier=tier,
                model=MODELS[tier],
                task_type=task_type,
                prompt=prompt,
                image_b64=image_b64,
                audit_id=audit_id,
                agent=agent,
                max_tokens=max_tokens,
            )
            if result is not None:
                return result

        return STATIC_FALLBACK

    def _fallback_chain(self, start: str) -> list[str]:
        idx = FALLBACK_ORDER.index(start) if start in FALLBACK_ORDER else 1
        return FALLBACK_ORDER[idx:]  # start tier → cheaper tiers

    async def _call(
        self,
        tier: str,
        model: str,
        task_type: str,
        prompt: str,
        image_b64: str | None,
        audit_id: str | None,
        agent: str | None,
        max_tokens: int,
    ) -> str | None:
        start = time.time()
        error_str = None
        tokens = 0
        cost_usd = 0.0

        try:
            messages = self._build_messages(prompt, image_b64)
            response = await self._client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.3,
            )
            tokens = response.usage.total_tokens if response.usage else 0
            cost_usd = round((tokens / 1000) * COST_PER_1K.get(tier, 0.001), 8)
            content = response.choices[0].message.content or ""
        except Exception as e:
            error_str = str(e)
            logger.warning(f"IronLabs [{model}] failed for {task_type}: {e}")
            content = None
        finally:
            latency_ms = int((time.time() - start) * 1000)
            await self._log(
                audit_id=audit_id,
                agent=agent or "",
                model=model,
                task_type=task_type,
                tokens=tokens,
                cost_usd=cost_usd,
                latency_ms=latency_ms,
                error=error_str,
            )

        return content

    def _build_messages(self, prompt: str, image_b64: str | None) -> list:
        if image_b64:
            return [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                    },
                ],
            }]
        return [{"role": "user", "content": prompt}]

    async def _log(
        self,
        audit_id: str | None,
        agent: str,
        model: str,
        task_type: str,
        tokens: int,
        cost_usd: float,
        latency_ms: int,
        error: str | None = None,
    ) -> None:
        ts = datetime.datetime.now(datetime.UTC).isoformat()
        try:
            with open(LOG_CSV_PATH, "a", newline="") as f:
                csv.writer(f).writerow(
                    [ts, audit_id, agent, model, task_type, tokens, cost_usd, latency_ms, error or ""]
                )
        except Exception as e:
            logger.debug(f"CSV log write failed: {e}")

        try:
            await log_ironlabs_call({
                "audit_id": audit_id or "",
                "agent": agent,
                "model": model,
                "task_type": task_type,
                "tokens": tokens,
                "cost_usd": cost_usd,
                "latency_ms": latency_ms,
            })
        except Exception as e:
            logger.debug(f"DB log write failed: {e}")
