import asyncio
import base64
import hashlib
import time
import logging
from pathlib import Path

from agents.intake import IntakeAgent
from agents.forensics import ForensicsAgent
from agents.clinical import ClinicalAgent
from agents.verdict import VerdictAgent
from agents.audit import AuditAgent
from db import next_audit_id

logger = logging.getLogger(__name__)

PIPELINE_TIMEOUT_SEC = 10


class AsyncOrchestrator:
    def __init__(self):
        self.intake   = IntakeAgent()
        self.forensics = ForensicsAgent()
        self.clinical  = ClinicalAgent()
        self.verdict   = VerdictAgent()
        self.audit     = AuditAgent()

    async def run(self, image_path: str, modality: str) -> dict:
        context = await self._build_context(image_path, modality)
        t0 = time.time()

        async def pipeline():
            # Stage 1 — parallel: Intake, Forensics, Clinical
            intake_r, forensics_r, clinical_r = await asyncio.gather(
                self.intake.execute(context),
                self.forensics.execute(context),
                self.clinical.execute(context),
                return_exceptions=True,
            )
            context["intake"]   = self._unwrap(intake_r,   "intake")
            context["forensics"] = self._unwrap(forensics_r, "forensics")
            context["clinical"]  = self._unwrap(clinical_r,  "clinical")

            # Stage 2 — Verdict (needs all three scores)
            context["verdict"] = await self.verdict.execute(context)

            # Stage 3 — Audit (DB write + webhooks)
            context["total_latency_ms"] = int((time.time() - t0) * 1000)
            context["audit"] = await self.audit.execute(context)

            return context

        try:
            result = await asyncio.wait_for(pipeline(), timeout=PIPELINE_TIMEOUT_SEC)
            return self._format_response(result, int((time.time() - t0) * 1000))
        except asyncio.TimeoutError:
            logger.error(f"Pipeline timeout for {context.get('audit_id')}")
            return self._timeout_response(context, int((time.time() - t0) * 1000))

    async def _build_context(self, image_path: str, modality: str) -> dict:
        file_bytes = Path(image_path).read_bytes()
        sha256 = hashlib.sha256(file_bytes).hexdigest()
        image_b64 = base64.b64encode(file_bytes).decode()
        audit_id = await next_audit_id()
        return {
            "image_path":  image_path,
            "image_b64":   image_b64,
            "sha256":      sha256,
            "modality":    modality,
            "audit_id":    audit_id,
            "total_cost_usd": 0.0,
        }

    def _unwrap(self, result, agent_name: str) -> dict:
        if isinstance(result, Exception):
            logger.warning(f"Agent {agent_name} raised: {result}")
            return {
                "agent": agent_name,
                "score": 0.5,
                "evidence": [],
                "latency_ms": 0,
                "error": str(result),
            }
        return result

    def _format_response(self, context: dict, total_latency_ms: int) -> dict:
        verdict_out = context.get("verdict", {})
        audit_out   = context.get("audit", {})

        all_evidence = []
        for agent_name in ("intake", "forensics", "clinical"):
            for e in context.get(agent_name, {}).get("evidence", []):
                if isinstance(e, dict) and e.get("type") != "stub":
                    all_evidence.append({
                        "type":         e.get("type", "unknown"),
                        "region":       e.get("region"),
                        "score":        e.get("score", 0.5),
                        "source_agent": agent_name,
                    })

        heatmap_url = None
        if context.get("heatmap_path"):
            heatmap_url = f"/static/heatmaps/{Path(context['heatmap_path']).name}"

        # Build agent_outputs without bulky image_b64
        agent_outputs = {}
        for key in ("intake", "forensics", "clinical", "verdict"):
            out = dict(context.get(key, {}))
            out.pop("image_b64", None)
            agent_outputs[key] = out

        return {
            "audit_id":        context["audit_id"],
            "verdict":         verdict_out.get("decision", "ESCALATE"),
            "confidence":      verdict_out.get("confidence", 0.5),
            "rationale":       verdict_out.get("rationale", ""),
            "evidence":        all_evidence,
            "heatmap_url":     heatmap_url,
            "agent_outputs":   agent_outputs,
            "total_latency_ms": total_latency_ms,
            "total_cost_usd":  audit_out.get("total_cost_usd", 0.0),
            "hash_chain": {
                "prev": audit_out.get("hash_prev", "GENESIS"),
                "self": audit_out.get("hash_self", ""),
            },
        }

    def _timeout_response(self, context: dict, total_latency_ms: int) -> dict:
        return {
            "audit_id":        context.get("audit_id", "AEG-TIMEOUT"),
            "verdict":         "ESCALATE",
            "confidence":      0.5,
            "rationale":       "Verification pipeline timed out after 10 seconds; human review required.",
            "evidence":        [],
            "heatmap_url":     None,
            "agent_outputs":   {},
            "total_latency_ms": total_latency_ms,
            "total_cost_usd":  0.0,
            "hash_chain":      {"prev": "GENESIS", "self": ""},
            "error":           "timeout",
        }
