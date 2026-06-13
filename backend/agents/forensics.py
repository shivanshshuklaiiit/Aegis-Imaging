"""
ForensicsAgent — P2 owns the real implementation.

This stub returns neutral scores so the orchestrator and Verdict Agent
can run end-to-end without P2's code.

CONTRACT (do not change these return keys without syncing with P1):
    score (float 0-1): trust score — higher = more likely genuine
    ai_probability (float 0-1): probability the image is AI-generated
    evidence (list): list of evidence dicts with keys: type, score, source_agent
    suspicious_regions (list): [{"bbox": [x1,y1,x2,y2], "label": str, "score": float}]
                                bbox values are 0-1 fractions of image dimensions

Context keys consumed:
    image_path (str): path to uploaded image file
    image_b64 (str): base64-encoded image (for vision LLM calls)
    sha256 (str): file hash (for HF result caching)
"""
from agents.base import BaseAgent


class ForensicsAgent(BaseAgent):
    name = "forensics"

    async def run(self, context: dict) -> dict:
        return {
            "score": 0.5,
            "ai_probability": 0.5,
            "evidence": [{"type": "stub", "score": 0.5, "source_agent": "forensics"}],
            "suspicious_regions": [],
            "_stub": True,
        }
