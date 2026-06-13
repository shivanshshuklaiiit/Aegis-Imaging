import os
import json
import hashlib
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from db import init_db, get_verification, get_dashboard_data
from orchestrator import AsyncOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

UPLOAD_DIR  = Path("data/uploads")
HEATMAP_DIR = Path("data/heatmaps")
DEMO_CACHE_DIR = Path("demo/cached_verdicts")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

MAX_FILE_BYTES = 20 * 1024 * 1024  # 20 MB
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".dcm"}
VALID_MODALITIES = {"xray", "mri", "ct", "ultrasound", "other"}

orchestrator = AsyncOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    for d in (UPLOAD_DIR, HEATMAP_DIR, Path("data")):
        d.mkdir(parents=True, exist_ok=True)
    await init_db()
    logger.info(f"Aegis Imaging backend started — DEMO_MODE={DEMO_MODE}")
    yield


app = FastAPI(title="Aegis Imaging API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

HEATMAP_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static/heatmaps", StaticFiles(directory=str(HEATMAP_DIR)), name="heatmaps")


# ─── Verify ───────────────────────────────────────────────────────────────────

@app.post("/api/v1/verify")
async def verify_image(
    file: UploadFile = File(...),
    modality: str = Form("other"),
):
    suffix = Path(file.filename or "upload").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(sorted(ALLOWED_SUFFIXES))}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=422, detail="File exceeds the 20 MB limit.")
    if len(file_bytes) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    if modality not in VALID_MODALITIES:
        modality = "other"

    sha256 = hashlib.sha256(file_bytes).hexdigest()
    save_path = UPLOAD_DIR / f"{sha256}{suffix}"
    save_path.write_bytes(file_bytes)

    if DEMO_MODE:
        cached = _load_demo_cache(sha256)
        if cached:
            logger.info(f"DEMO_MODE: serving cached verdict for {sha256[:8]}")
            return JSONResponse(content=cached)

    logger.info(f"Running pipeline for {sha256[:8]} modality={modality}")
    result = await orchestrator.run(str(save_path), modality)
    return JSONResponse(content=result)


# ─── Audit detail ─────────────────────────────────────────────────────────────

@app.get("/api/v1/audit/{audit_id}")
async def get_audit(audit_id: str):
    record = await get_verification(audit_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Audit record '{audit_id}' not found.")

    parsed = {}
    for field in ("intake", "forensics", "clinical"):
        raw = record.get(f"{field}_json")
        try:
            parsed[field] = json.loads(raw) if raw else {}
        except Exception:
            parsed[field] = {}

    heatmap_url = None
    if record.get("heatmap_path"):
        heatmap_url = f"/static/heatmaps/{Path(record['heatmap_path']).name}"

    return {
        "audit_id":    record["audit_id"],
        "verdict":     record["verdict"],
        "confidence":  record["confidence"],
        "rationale":   record["rationale"],
        "evidence":    [],
        "heatmap_url": heatmap_url,
        "agent_outputs": parsed,
        "total_latency_ms": record["total_latency_ms"],
        "total_cost_usd":   record["total_cost_usd"],
        "hash_chain": {
            "prev": record["hash_prev"],
            "self": record["hash_self"],
        },
        "created_at":   record["created_at"],
        "image_sha256": record["image_sha256"],
        "modality":     record["modality"],
    }


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/api/v1/dashboard")
async def dashboard():
    return await get_dashboard_data()


# ─── Mock webhook receivers (P4 owns the real versions) ───────────────────────

@app.post("/mock-ehr")
async def mock_ehr(request: Request):
    payload = await request.json()
    _append_notification_log("mock-ehr", payload)
    return {"status": "received", "endpoint": "mock-ehr"}


@app.post("/mock-claims")
async def mock_claims(request: Request):
    payload = await request.json()
    _append_notification_log("mock-claims", payload)
    return {"status": "received", "endpoint": "mock-claims"}


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "demo_mode": DEMO_MODE}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _load_demo_cache(sha256: str) -> dict | None:
    if not DEMO_CACHE_DIR.exists():
        return None
    for f in DEMO_CACHE_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text())
            if data.get("image_sha256") == sha256:
                return data
        except Exception:
            pass
    return None


def _append_notification_log(endpoint: str, payload: dict) -> None:
    import datetime
    log_path = Path("data/notifications.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.datetime.utcnow().isoformat(),
        "endpoint": endpoint,
        "payload": payload,
    }
    try:
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass
