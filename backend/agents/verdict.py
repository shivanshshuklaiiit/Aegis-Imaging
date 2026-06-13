import json
import logging
from agents.base import BaseAgent
from ironlabs_router import IronLabsRouter

logger = logging.getLogger(__name__)

WEIGHTS = {"intake": 0.2, "forensics": 0.5, "clinical": 0.3}
APPROVE_THRESHOLD = 0.75
REJECT_THRESHOLD  = 0.35


class VerdictAgent(BaseAgent):
    name = "verdict"

    def __init__(self):
        self.router = IronLabsRouter()

    async def run(self, context: dict) -> dict:
        scores = {
            k: context.get(k, {}).get("score", 0.5)
            for k in ("intake", "forensics", "clinical")
        }
        weighted = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)

        if weighted >= APPROVE_THRESHOLD:
            decision = "APPROVE"
        elif weighted <= REJECT_THRESHOLD:
            decision = "REJECT"
        else:
            decision = "ESCALATE"

        prompt = self._build_prompt(context, decision, weighted)
        rationale = await self.router.route(
            task_type="critical_decision",
            prompt=prompt,
            audit_id=context.get("audit_id"),
            agent=self.name,
        )

        # Collect all evidence from upstream agents
        evidence = []
        for agent_name in ("intake", "forensics", "clinical"):
            for e in context.get(agent_name, {}).get("evidence", []):
                if isinstance(e, dict) and e.get("type") != "stub":
                    evidence.append({**e, "source_agent": agent_name})

        return {
            "score": round(weighted, 4),
            "decision": decision,
            "confidence": round(weighted if decision != "ESCALATE" else 0.5, 4),
            "rationale": rationale,
            "weighted_total": round(weighted, 4),
            "component_scores": scores,
            "evidence": evidence,
        }

    def _build_prompt(self, ctx: dict, decision: str, weighted: float) -> str:
        def _safe(key: str) -> str:
            val = ctx.get(key, {})
            try:
                return json.dumps({k: v for k, v in val.items() if k not in ("evidence", "image_b64")})
            except Exception:
                return "{}"

        return f"""You are the Chief Verification Officer for Aegis Imaging.

Three specialist agents reported on a medical image submission:
- Intake/Metadata Agent: {_safe('intake')}
- Visual Forensics Agent: {_safe('forensics')}
- Clinical Plausibility Agent: {_safe('clinical')}

Weighted trust score: {weighted:.2f} (scale 0.0–1.0, higher = more trustworthy)
Final decision: {decision}

Write a 2–3 sentence human-readable rationale for this decision in the voice of a clinical compliance officer. Be specific about the evidence that drove the decision. Do not include any preamble or meta-commentary."""
