"""
HuggingFace AI-image detectors.

Calls two models in parallel and returns an ensemble score.
Results are cached by SHA-256 to avoid repeated cold-start costs.

Known gotcha: HF inference cold starts can take 20-30s on free tier.
Pre-warm by calling detect_ai() with a dummy image at startup.
"""

import asyncio
import hashlib
import json
import os
from pathlib import Path

import httpx

HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

CACHE_DIR = Path("data/hf_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Models to query (in parallel). Add/remove here as needed.
# Verify response schema by printing raw result on first run — docs are wrong.
DETECTORS = [
    "Organika/sdxl-detector",
    "umm-maybe/AI-image-detector",
]
DETECTOR_TIMEOUT_SEC = 15


async def _call_one(client: httpx.AsyncClient, model: str, image_bytes: bytes) -> dict:
    url = f"https://api-inference.huggingface.co/models/{model}"
    try:
        r = await client.post(
            url,
            headers=HF_HEADERS,
            content=image_bytes,
            timeout=DETECTOR_TIMEOUT_SEC,
        )
        r.raise_for_status()
        return {"model": model, "result": r.json()}
    except Exception as e:
        return {"model": model, "error": str(e)}


def _extract_score(raw_result: list) -> float | None:
    """
    HF classifiers return a list like:
      [{"label": "artificial", "score": 0.92}, {"label": "real", "score": 0.08}]
    Label names vary per model — match on 'fake', 'ai', 'artificial', 'generated'.
    Returns the AI-probability score, or None if unparseable.
    """
    ai_keywords = {"fake", "ai", "artificial", "generated", "synthetic"}
    for item in raw_result:
        if any(kw in item.get("label", "").lower() for kw in ai_keywords):
            return float(item["score"])
    return None


async def detect_ai(image_bytes: bytes) -> dict:
    """
    Run all configured detectors in parallel.

    Returns:
      {
        "ensemble_score": float,   # 0.0 = certainly real, 1.0 = certainly AI
        "evidence": list[dict],
      }
    """
    sha = hashlib.sha256(image_bytes).hexdigest()
    cache_path = CACHE_DIR / f"{sha}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    async with httpx.AsyncClient() as client:
        raw_results = await asyncio.gather(
            *[_call_one(client, m, image_bytes) for m in DETECTORS]
        )

    scores: list[float] = []
    evidence: list[dict] = []

    for r in raw_results:
        if "error" in r:
            evidence.append({"detector": r["model"], "error": r["error"]})
            continue
        score = _extract_score(r["result"])
        if score is not None:
            scores.append(score)
            evidence.append({"detector": r["model"], "label": "ai", "score": score})
        else:
            # Log raw response so we can fix the parser
            evidence.append({"detector": r["model"], "raw": r["result"], "parse_error": True})

    ensemble_score = sum(scores) / len(scores) if scores else 0.5
    out = {"ensemble_score": ensemble_score, "evidence": evidence}
    cache_path.write_text(json.dumps(out))
    return out


async def warmup() -> None:
    """Call once at application startup to avoid cold-start delays during demo."""
    import base64
    # Minimal 1x1 white PNG
    dummy = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwADhQGAWjR9awAAAABJRU5ErkJggg=="
    )
    await detect_ai(dummy)
