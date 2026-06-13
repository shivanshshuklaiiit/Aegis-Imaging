"""
ClinicalAgent — anatomy plausibility check using a vision LLM (Claude Haiku via IronLabs).

Returns:
  score       = plausibility (1.0 = perfectly real anatomy, 0.0 = impossible anatomy)
  evidence    = list of specific impossibilities the LLM found
  suspicious_regions = same impossibilities in heatmap-compatible format
"""

import base64
import json
import re
from pathlib import Path

from agents.base import BaseAgent
from ironlabs_router import IronLabsRouter

_CLINICAL_PROMPT = """\
You are a board-certified radiologist reviewing a medical image submitted for authenticity verification.

Step 1: Describe what you see — anatomical region, imaging modality, view/plane, key visible features.
Step 2: Rate clinical plausibility from 0.0 to 1.0:
  - 1.0 = anatomy fully obeys normal physiology, no anomalies
  - 0.0 = impossible anatomy that cannot exist in a real patient
  Consider: impossible organ shapes, mirrored asymmetry, unnatural densities or textures,
            labels/markers inconsistent with real imaging equipment.
Step 3: List each impossibility with an approximate bounding box as image-coordinate fractions (0–1).

Output strict JSON only — no preamble, no markdown fences:
{
  "description": "<brief radiologist-style description>",
  "plausibility": 0.85,
  "impossibilities": [
    {
      "description": "<specific finding, e.g. fourth rib bifurcates unnaturally>",
      "bbox": [0.4, 0.3, 0.55, 0.45]
    }
  ]
}
bbox format: [x1, y1, x2, y2] as fractions of image width/height."""


class ClinicalAgent(BaseAgent):
    name = "clinical"

    def __init__(self) -> None:
        self.router = IronLabsRouter()

    async def run(self, context: dict) -> dict:
        # Reuse image_b64 from ForensicsAgent if already computed
        image_b64 = context.get("image_b64")
        if not image_b64:
            image_b64 = base64.b64encode(Path(context["image_path"]).read_bytes()).decode()

        raw = await self.router.route_vision("clinical_vision", _CLINICAL_PROMPT, image_b64)
        parsed = _parse_json(raw)

        plausibility = float(parsed.get("plausibility", 0.5))
        impossibilities = parsed.get("impossibilities", [])
        ai_signal = 1.0 - plausibility  # high plausibility → low AI signal

        evidence = [
            {
                "detector": "clinical_llm",
                "description": imp["description"],
                "score": round(ai_signal, 3),
            }
            for imp in impossibilities
        ]
        suspicious_regions = [
            {
                "description": imp["description"],
                "label": "clinical_anomaly",
                "bbox": imp.get("bbox", []),
                "score": round(ai_signal, 3),
            }
            for imp in impossibilities
        ]

        return {
            "score": round(plausibility, 4),
            "plausibility": round(plausibility, 4),
            "description": parsed.get("description", ""),
            "evidence": evidence,
            "suspicious_regions": suspicious_regions,
        }


def _parse_json(text: str) -> dict:
    """Try strict parse, then regex-extract JSON block, then return safe fallback."""
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
    return {"plausibility": 0.5, "impossibilities": [], "description": "parse_error"}
