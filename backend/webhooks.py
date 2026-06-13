import os
import json
import logging
import datetime
from pathlib import Path

import httpx
from db import log_ehr_event

logger = logging.getLogger(__name__)

MOCK_EHR_URL    = os.getenv("MOCK_EHR_URL",    "http://localhost:8000/mock-ehr")
MOCK_CLAIMS_URL = os.getenv("MOCK_CLAIMS_URL", "http://localhost:8000/mock-claims")
NOTIFICATIONS_LOG = Path("data/notifications.log")


async def fire_all(audit_id: str, verdict: str, context: dict) -> None:
    ehr_payload = {
        "resourceType": "AuditEvent",
        "audit_id": audit_id,
        "verdict": verdict,
        "modality": context.get("modality"),
        "image_sha256": context.get("sha256"),
        "confidence": context.get("verdict", {}).get("confidence", 0.5),
        "rationale": context.get("verdict", {}).get("rationale", ""),
    }
    claims_payload = {
        "claim_verification_id": audit_id,
        "result": verdict,
        "image_hash": context.get("sha256"),
        "confidence_score": context.get("verdict", {}).get("confidence", 0.5),
        "rationale": context.get("verdict", {}).get("rationale", ""),
    }

    for endpoint, url, payload in [
        ("mock-ehr",    MOCK_EHR_URL,    ehr_payload),
        ("mock-claims", MOCK_CLAIMS_URL, claims_payload),
    ]:
        _write_to_log(audit_id, endpoint, payload)
        try:
            await log_ehr_event(audit_id, endpoint, payload)
        except Exception as e:
            logger.debug(f"DB webhook log failed: {e}")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(url, json=payload)
        except Exception as e:
            logger.debug(f"Webhook {endpoint} delivery failed (non-fatal): {e}")


def _write_to_log(audit_id: str, endpoint: str, payload: dict) -> None:
    NOTIFICATIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.datetime.now(datetime.UTC).isoformat(),
        "audit_id": audit_id,
        "endpoint": endpoint,
        "payload": payload,
    }
    try:
        with open(NOTIFICATIONS_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.debug(f"Notification log write failed: {e}")
