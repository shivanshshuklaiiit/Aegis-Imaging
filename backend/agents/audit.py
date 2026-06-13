import json
import logging
from agents.base import BaseAgent
from db import get_last_hash, compute_chain_hash, insert_verification, get_audit_cost
import webhooks

logger = logging.getLogger(__name__)


class AuditAgent(BaseAgent):
    name = "audit"

    async def run(self, context: dict) -> dict:
        verdict_out = context.get("verdict", {})
        audit_id = context["audit_id"]

        prev_hash = await get_last_hash()

        # Canonical record that gets hashed — must be deterministic
        chain_input = {
            "audit_id": audit_id,
            "image_sha256": context["sha256"],
            "verdict": verdict_out.get("decision", "ESCALATE"),
            "confidence": verdict_out.get("confidence", 0.5),
            "intake_score": context.get("intake", {}).get("score", 0.0),
            "forensics_score": context.get("forensics", {}).get("score", 0.0),
            "clinical_score": context.get("clinical", {}).get("score", 0.0),
        }
        hash_self = compute_chain_hash(prev_hash, chain_input)

        total_cost = await get_audit_cost(audit_id)

        db_record = {
            "audit_id": audit_id,
            "image_sha256": context["sha256"],
            "image_path": context["image_path"],
            "heatmap_path": context.get("heatmap_path"),
            "modality": context.get("modality", "other"),
            "verdict": verdict_out.get("decision", "ESCALATE"),
            "confidence": verdict_out.get("confidence", 0.5),
            "rationale": verdict_out.get("rationale", ""),
            "intake_json": json.dumps(context.get("intake", {})),
            "forensics_json": json.dumps(context.get("forensics", {})),
            "clinical_json": json.dumps(context.get("clinical", {})),
            "orchestrator_json": json.dumps({
                "weighted_total": verdict_out.get("weighted_total"),
                "component_scores": verdict_out.get("component_scores"),
            }),
            "total_latency_ms": context.get("total_latency_ms", 0),
            "total_cost_usd": total_cost,
            "hash_prev": prev_hash,
            "hash_self": hash_self,
        }

        try:
            await insert_verification(db_record)
        except Exception as e:
            logger.error(f"DB write failed for {audit_id}: {e} — verdict still returned to caller")

        try:
            await webhooks.fire_all(audit_id, verdict_out.get("decision", "ESCALATE"), context)
        except Exception as e:
            logger.warning(f"Webhook fire failed for {audit_id}: {e}")

        return {
            "hash_prev": prev_hash,
            "hash_self": hash_self,
            "audit_id": audit_id,
            "total_cost_usd": total_cost,
            "evidence": [],
        }
