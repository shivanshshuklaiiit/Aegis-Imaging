"""
HuggingFace AI-image detectors. P2 owns the full implementation.
This file is a functional stub that returns neutral scores.
P2 replaces the body of detect_ai() with real HF inference calls.
"""
import os
import json
import hashlib
import asyncio
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}
CACHE_DIR = Path("data/hf_cache")

DETECTORS = [
    "Organika/sdxl-detector",
    "umm-maybe/AI-image-detector",
]


async def detect_ai(image_bytes: bytes) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    sha = hashlib.sha256(image_bytes).hexdigest()
    cache_path = CACHE_DIR / f"{sha}.json"

    if cache_path.exists():
        return json.loads(cache_path.read_text())

    if not HF_TOKEN:
        logger.warning("HF_TOKEN not set — returning stub detector result")
        return _stub_result()

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            *[_call_one(client, model, image_bytes) for model in DETECTORS],
            return_exceptions=True,
        )

    scores = []
    evidence = []
    for r in results:
        if isinstance(r, Exception) or "error" in r:
            evidence.append({"detector": r.get("model", "unknown") if isinstance(r, dict) else "unknown", "error": str(r)})
            continue
        for item in r.get("result", []):
            label = item.get("label", "").lower()
            if "fake" in label or "ai" in label or "artificial" in label:
                scores.append(item["score"])
                evidence.append({
                    "detector": r["model"],
                    "label": item["label"],
                    "score": item["score"],
                })

    ensemble_score = sum(scores) / len(scores) if scores else 0.5
    out = {"ensemble_score": ensemble_score, "evidence": evidence}
    cache_path.write_text(json.dumps(out))
    return out


async def _call_one(client: httpx.AsyncClient, model: str, image_bytes: bytes) -> dict:
    url = f"https://api-inference.huggingface.co/models/{model}"
    try:
        r = await client.post(url, headers=HF_HEADERS, content=image_bytes, timeout=20.0)
        r.raise_for_status()
        return {"model": model, "result": r.json()}
    except Exception as e:
        return {"model": model, "error": str(e)}


def _stub_result() -> dict:
    return {
        "ensemble_score": 0.5,
        "evidence": [{"detector": "stub", "note": "HF_TOKEN not configured"}],
        "_stub": True,
    }
