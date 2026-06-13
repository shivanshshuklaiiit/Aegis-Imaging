"""
ForensicsAgent — visual AI-detection using:
  1. HuggingFace image classifiers (parallel HTTP)
  2. FFT frequency analysis (CPU, run in thread pool)
  3. Vision LLM via IronLabs (GPT-4o-mini)

Returns a trust_score: 1.0 = certainly real, 0.0 = certainly AI.
Also populates context["image_b64"] so ClinicalAgent can reuse it.
"""

import asyncio
import base64
import json
import re
from pathlib import Path

from agents.base import BaseAgent
from fft_analysis import analyze_fft
from hf_detectors import detect_ai
from ironlabs_router import IronLabsRouter

_FORENSICS_PROMPT = """\
You are a digital forensics expert analyzing a medical image for signs of AI generation.

Inspect the image for:
1. Unnatural textures or patterns characteristic of SDXL / diffusion models
2. Frequency artifacts, grid patterns, or repeating tiling structures
3. Inconsistent noise or grain distribution across regions
4. Areas that appear artificially smoothed or impossibly sharp

Output strict JSON only — no preamble, no markdown:
{
  "ai_prob": 0.85,
  "evidence": [
    {"detector": "llm_vision", "description": "<specific observation>", "score": 0.85}
  ],
  "regions": [
    {"description": "<what looks wrong>", "bbox": [0.2, 0.3, 0.5, 0.6]}
  ]
}
bbox values are fractions (0-1) of image width/height: [x1, y1, x2, y2]."""


class ForensicsAgent(BaseAgent):
    name = "forensics"

    def __init__(self) -> None:
        self.router = IronLabsRouter()

    async def run(self, context: dict) -> dict:
        image_path = context["image_path"]
        image_bytes = Path(image_path).read_bytes()

        # Encode once; store in context so ClinicalAgent reuses without re-reading
        image_b64 = base64.b64encode(image_bytes).decode()
        context["image_b64"] = image_b64

        # All three analyses in parallel
        hf_r, fft_r, llm_r = await asyncio.gather(
            detect_ai(image_bytes),
            asyncio.to_thread(analyze_fft, image_bytes),
            self._llm_forensics(image_b64),
        )

        ai_prob = (
            0.5 * hf_r["ensemble_score"]
            + 0.2 * fft_r["score"]
            + 0.3 * llm_r["ai_prob"]
        )
        trust_score = 1.0 - ai_prob

        return {
            "score": round(trust_score, 4),
            "ai_probability": round(ai_prob, 4),
            "evidence": [
                *hf_r["evidence"],
                *fft_r["evidence"],
                *llm_r.get("evidence", []),
            ],
            "suspicious_regions": llm_r.get("regions", []),
        }

    async def _llm_forensics(self, image_b64: str) -> dict:
        raw = await self.router.route_vision("forensics_vision", _FORENSICS_PROMPT, image_b64)
        parsed = _parse_json(raw, fallback={})
        # Normalise: always return required keys even if LLM returned error/partial JSON
        return {
            "ai_prob": float(parsed.get("ai_prob", 0.5)),
            "evidence": parsed.get("evidence", []),
            "regions": parsed.get("regions", []),
        }


def _parse_json(text: str, fallback: dict) -> dict:
    """Try strict parse, then regex-extract JSON block, then return fallback."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, TypeError):
            pass
    return fallback
