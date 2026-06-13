import os
import json
import hashlib
import aiosqlite
from datetime import datetime, UTC
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "data/aegis.db")

_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS verifications (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_id          TEXT UNIQUE NOT NULL,
        created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        image_sha256      TEXT NOT NULL,
        image_path        TEXT NOT NULL,
        heatmap_path      TEXT,
        modality          TEXT,
        verdict           TEXT CHECK(verdict IN ('APPROVE','REJECT','ESCALATE')),
        confidence        REAL,
        rationale         TEXT,
        intake_json       TEXT,
        forensics_json    TEXT,
        clinical_json     TEXT,
        orchestrator_json TEXT,
        total_latency_ms  INTEGER,
        total_cost_usd    REAL,
        hash_prev         TEXT,
        hash_self         TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS ironlabs_calls (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_id    TEXT,
        agent       TEXT,
        model       TEXT,
        task_type   TEXT,
        tokens      INTEGER,
        cost_usd    REAL,
        latency_ms  INTEGER,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS mock_ehr_events (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_id     TEXT,
        endpoint     TEXT,
        payload_json TEXT,
        received_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_ver_audit_id  ON verifications(audit_id)",
    "CREATE INDEX IF NOT EXISTS idx_ver_created   ON verifications(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_il_audit_id   ON ironlabs_calls(audit_id)",
]


async def init_db() -> None:
    Path(DATABASE_URL).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DATABASE_URL) as db:
        for stmt in _SCHEMA:
            await db.execute(stmt)
        await db.commit()


# ---------- hash chain ----------

def compute_chain_hash(prev_hash: str, record: dict) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
    payload = (prev_hash or "GENESIS") + canonical
    return hashlib.sha256(payload.encode()).hexdigest()


async def get_last_hash() -> str:
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute(
            "SELECT hash_self FROM verifications ORDER BY id DESC LIMIT 1"
        ) as cur:
            row = await cur.fetchone()
            return row[0] if row else "GENESIS"


# ---------- audit id ----------

async def next_audit_id() -> str:
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute("SELECT COUNT(*) + 1 FROM verifications") as cur:
            row = await cur.fetchone()
            seq = row[0] if row else 1
    return f"AEG-{datetime.now(UTC).strftime('%Y%m%d')}-{seq:05d}"


# ---------- writes ----------

async def insert_verification(record: dict) -> None:
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            INSERT INTO verifications (
                audit_id, image_sha256, image_path, heatmap_path, modality,
                verdict, confidence, rationale,
                intake_json, forensics_json, clinical_json, orchestrator_json,
                total_latency_ms, total_cost_usd, hash_prev, hash_self
            ) VALUES (
                :audit_id, :image_sha256, :image_path, :heatmap_path, :modality,
                :verdict, :confidence, :rationale,
                :intake_json, :forensics_json, :clinical_json, :orchestrator_json,
                :total_latency_ms, :total_cost_usd, :hash_prev, :hash_self
            )
            """,
            record,
        )
        await db.commit()


async def log_ironlabs_call(entry: dict) -> None:
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            """
            INSERT INTO ironlabs_calls (audit_id, agent, model, task_type, tokens, cost_usd, latency_ms)
            VALUES (:audit_id, :agent, :model, :task_type, :tokens, :cost_usd, :latency_ms)
            """,
            entry,
        )
        await db.commit()


async def log_ehr_event(audit_id: str, endpoint: str, payload: dict) -> None:
    async with aiosqlite.connect(DATABASE_URL) as db:
        await db.execute(
            "INSERT INTO mock_ehr_events (audit_id, endpoint, payload_json) VALUES (?, ?, ?)",
            (audit_id, endpoint, json.dumps(payload)),
        )
        await db.commit()


# ---------- reads ----------

async def get_verification(audit_id: str) -> dict | None:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM verifications WHERE audit_id = ?", (audit_id,)
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_audit_cost(audit_id: str) -> float:
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute(
            "SELECT COALESCE(SUM(cost_usd), 0.0) FROM ironlabs_calls WHERE audit_id = ?",
            (audit_id,),
        ) as cur:
            row = await cur.fetchone()
            return float(row[0]) if row else 0.0


async def get_dashboard_data() -> dict:
    async with aiosqlite.connect(DATABASE_URL) as db:
        db.row_factory = aiosqlite.Row

        async with db.execute(
            """
            SELECT verdict, COUNT(*) as count FROM verifications
            WHERE DATE(created_at) = DATE('now') GROUP BY verdict
            """
        ) as cur:
            verdict_counts = {r["verdict"]: r["count"] for r in await cur.fetchall()}

        async with db.execute(
            """
            SELECT AVG(total_latency_ms) as avg_ms, MAX(total_latency_ms) as max_ms
            FROM verifications WHERE DATE(created_at) = DATE('now')
            """
        ) as cur:
            latency = await cur.fetchone()

        async with db.execute(
            "SELECT model, SUM(cost_usd) as total FROM ironlabs_calls GROUP BY model"
        ) as cur:
            cost_by_model = {r["model"]: round(r["total"], 6) for r in await cur.fetchall()}

        async with db.execute(
            """
            SELECT audit_id, verdict, confidence, total_latency_ms, total_cost_usd, created_at
            FROM verifications ORDER BY created_at DESC LIMIT 20
            """
        ) as cur:
            recent = [dict(r) for r in await cur.fetchall()]

    total_today = sum(verdict_counts.values())
    total_cost = sum(cost_by_model.values())

    # Savings vs always using the top tier model
    async with aiosqlite.connect(DATABASE_URL) as db:
        async with db.execute("SELECT SUM(tokens) FROM ironlabs_calls") as cur:
            row = await cur.fetchone()
            total_tokens = row[0] or 0

    top_tier_cost_per_1k = 0.015
    hypothetical_top_cost = (total_tokens / 1000) * top_tier_cost_per_1k
    saved = max(0.0, hypothetical_top_cost - total_cost)
    saved_pct = (saved / hypothetical_top_cost * 100) if hypothetical_top_cost > 0 else 0.0

    avg_ms = int(latency["avg_ms"] or 0)
    max_ms = int(latency["max_ms"] or 0)

    return {
        "totals": {
            "verifications_today": total_today,
            "approve": verdict_counts.get("APPROVE", 0),
            "reject": verdict_counts.get("REJECT", 0),
            "escalate": verdict_counts.get("ESCALATE", 0),
        },
        "latency": {"p50_ms": avg_ms, "p95_ms": max_ms},
        "cost": {
            "total_usd": round(total_cost, 6),
            "by_model": cost_by_model,
            "saved_vs_top_tier_usd": round(saved, 6),
            "saved_percent": round(saved_pct, 1),
        },
        "recent_audits": recent,
    }
