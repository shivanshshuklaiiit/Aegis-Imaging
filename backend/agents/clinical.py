"""
ClinicalAgent — P2 owns the real implementation.

This stub returns neutral scores so the orchestrator and Verdict Agent
can run end-to-end without P2's code.

CONTRACT (do not change these return keys without syncing with P1):
    score (float 0-1): clinical plausibility — higher = more anatomically plausible
    plausibility (float 0-1): same as score (alias for readability)
    description (str): brief description of the image content
    impossibilities (list): [{"description": str, "bbox": [x1,y1,x2,y2]}]
                             bbox values are 0-1 fractions of image dimensions
    evidence (list): list of evidence dicts with keys: type, score, source_agent

Context keys consumed:
    image_b64 (str): base64-encoded image for vision LLM
    modality (str): "xray" | "mri" | "ct" | "ultrasound" | "other"
"""
from agents.base import BaseAgent


class ClinicalAgent(BaseAgent):
    name = "clinical"

    async def run(self, context: dict) -> dict:
        return {
            "score": 0.5,
            "plausibility": 0.5,
            "description": "Clinical analysis pending — agent not yet implemented.",
            "impossibilities": [],
            "evidence": [{"type": "stub", "score": 0.5, "source_agent": "clinical"}],
            "_stub": True,
        }
