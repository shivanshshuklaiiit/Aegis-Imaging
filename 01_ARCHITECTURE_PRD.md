# Aegis Imaging — Architecture PRD

**Version:** 1.0
**Date:** June 13, 2026
**Owner:** Shiv (P1)
**Status:** Locked at H2 sync

---

## 1. Purpose

This document defines the technical architecture of Aegis Imaging. It is the single source of truth for system design, component contracts, and data flow. Any deviation must be agreed at a team sync.

---

## 2. System Overview

Aegis Imaging is a 3-tier application:

1. **Presentation layer** — React SPA served via Vite dev server (port 5173)
2. **Application layer** — FastAPI service (port 8000) hosting the agent orchestrator
3. **Data layer** — SQLite database, local filesystem for images, IronLabs + HuggingFace as external services

The core innovation is the **multi-agent orchestrator** that fans out work in parallel and aggregates verdicts.

---

## 3. High-Level Architecture Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                          USER BROWSER                              │
│                                                                    │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────┐ │
│  │   Upload    │  │  Verifying   │  │   Result    │  │Dashboard │ │
│  │    Page     │  │     Page     │  │    Pages    │  │   Page   │ │
│  └─────────────┘  └──────────────┘  └─────────────┘  └──────────┘ │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ HTTPS / JSON
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                  FASTAPI APPLICATION (port 8000)                   │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                  ROUTES (main.py)                          │    │
│  │  POST /api/v1/verify       GET /api/v1/audit/{id}          │    │
│  │  GET  /api/v1/dashboard    POST /mock-ehr  POST /mock-claims│   │
│  └────────────────┬───────────────────────────────────────────┘    │
│                   ▼                                                │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │            ASYNC ORCHESTRATOR (orchestrator.py)            │    │
│  │                                                            │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐   PARALLEL       │    │
│  │  │  AGENT 1 │  │  AGENT 2 │  │  AGENT 3 │ ← (gather)       │    │
│  │  │  Intake  │  │ Forensics│  │ Clinical │                  │    │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │    │
│  │       └─────────────┼─────────────┘                        │    │
│  │                     ▼                                      │    │
│  │              ┌───────────────┐                             │    │
│  │              │   AGENT 4     │                             │    │
│  │              │  Verdict      │                             │    │
│  │              └───────┬───────┘                             │    │
│  │                      ▼                                     │    │
│  │              ┌───────────────┐                             │    │
│  │              │   AGENT 5     │                             │    │
│  │              │   Audit       │                             │    │
│  │              └───────────────┘                             │    │
│  └────────────────────────────────────────────────────────────┘    │
│                   │                                                │
│  ┌────────────────┴────────────────┐                               │
│  ▼                                 ▼                               │
│ ┌──────────────────────┐  ┌─────────────────────┐                  │
│ │ IronLabsRouter       │  │ HFDetectors         │                  │
│ │ (ironlabs_router.py) │  │ (hf_detectors.py)   │                  │
│ └──────────┬───────────┘  └──────────┬──────────┘                  │
│            │                         │                             │
└────────────┼─────────────────────────┼─────────────────────────────┘
             │                         │
             ▼                         ▼
   ┌────────────────────┐  ┌─────────────────────────┐
   │ IronLabs API       │  │ HuggingFace Inference   │
   │ (cheap/mid/top LLM)│  │ (SDXL detector, etc.)   │
   └────────────────────┘  └─────────────────────────┘

             ┌──────────────────────────────────┐
             │       LOCAL DATA LAYER           │
             │                                  │
             │  ┌──────────────────────────┐    │
             │  │  SQLite: aegis.db        │    │
             │  │  - verifications         │    │
             │  │  - ironlabs_calls        │    │
             │  │  - mock_ehr_events       │    │
             │  └──────────────────────────┘    │
             │                                  │
             │  ┌──────────────────────────┐    │
             │  │  Filesystem              │    │
             │  │  /data/uploads/          │    │
             │  │  /data/heatmaps/         │    │
             │  │  /data/notifications.log │    │
             │  │  /data/ironlabs_log.csv  │    │
             │  └──────────────────────────┘    │
             └──────────────────────────────────┘
```

---

## 4. Component Contracts

### 4.1 Agent Interface (Python)

Every agent implements this base interface:

```python
from abc import ABC, abstractmethod
from typing import Any

class BaseAgent(ABC):
    name: str

    @abstractmethod
    async def run(self, context: dict) -> dict:
        """
        Args:
          context: shared dict with image_path, sha256, modality,
                   and outputs from prior agents
        Returns:
          dict with at minimum: {agent: str, score: float,
                                 evidence: list, latency_ms: int, error: str|None}
        """
        ...
```

### 4.2 API Contract — `POST /api/v1/verify`

**Request (multipart):**
```
file: <binary>
modality: "xray" | "mri" | "ct" | "ultrasound" | "other"
```

**Response:**
```json
{
  "audit_id": "AEG-20260613-00042",
  "verdict": "REJECT",
  "confidence": 0.91,
  "rationale": "Image shows characteristic SDXL frequency artifacts...",
  "evidence": [
    {
      "type": "frequency_artifact",
      "region": [120, 80, 200, 180],
      "score": 0.87,
      "source_agent": "forensics"
    }
  ],
  "heatmap_url": "/static/heatmaps/AEG-20260613-00042.png",
  "agent_outputs": {
    "intake": { "score": 0.2, "metadata_complete": false, "anomalies": [...] },
    "forensics": { "score": 0.87, "ai_probability": 0.92 },
    "clinical": { "score": 0.85, "plausibility": 0.15 },
    "verdict": { "score": 0.91, "weighted_total": 0.81 }
  },
  "total_latency_ms": 1840,
  "total_cost_usd": 0.0031,
  "hash_chain": {
    "prev": "a7f3...",
    "self": "b9e2..."
  }
}
```

### 4.3 API Contract — `GET /api/v1/audit/{audit_id}`

Returns full audit record (same shape as above plus timestamps and image URL).

### 4.4 API Contract — `GET /api/v1/dashboard`

```json
{
  "totals": {
    "verifications_today": 47,
    "approve": 32, "reject": 11, "escalate": 4
  },
  "latency": { "p50_ms": 1840, "p95_ms": 3200 },
  "cost": {
    "total_usd": 0.142,
    "by_model": { "llama-3.1-8b-instruct": 0.018, "gpt-4o-mini": 0.084, ... },
    "saved_vs_top_tier_usd": 0.31,
    "saved_percent": 68.6
  },
  "recent_audits": [ ... ]
}
```

---

## 5. Data Model

### 5.1 SQLite Schema

```sql
-- Primary verification record
CREATE TABLE verifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  audit_id TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  -- Image identity
  image_sha256 TEXT NOT NULL,
  image_path TEXT NOT NULL,
  heatmap_path TEXT,
  modality TEXT,

  -- Verdict
  verdict TEXT CHECK(verdict IN ('APPROVE','REJECT','ESCALATE')),
  confidence REAL,
  rationale TEXT,

  -- Agent outputs (JSON)
  intake_json TEXT,
  forensics_json TEXT,
  clinical_json TEXT,
  orchestrator_json TEXT,

  -- Metrics
  total_latency_ms INTEGER,
  total_cost_usd REAL,

  -- Hash chain (tamper-evident)
  hash_prev TEXT,
  hash_self TEXT NOT NULL
);

CREATE INDEX idx_verifications_audit_id ON verifications(audit_id);
CREATE INDEX idx_verifications_created_at ON verifications(created_at);

-- Per-LLM-call telemetry for IronLabs dashboard
CREATE TABLE ironlabs_calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  audit_id TEXT,
  agent TEXT,
  model TEXT,
  task_type TEXT,
  tokens INTEGER,
  cost_usd REAL,
  latency_ms INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ironlabs_calls_audit_id ON ironlabs_calls(audit_id);

-- Mock EHR/claims webhook log
CREATE TABLE mock_ehr_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  audit_id TEXT,
  endpoint TEXT,
  payload_json TEXT,
  received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 Hash Chain Algorithm

```python
def compute_chain_hash(prev_hash: str, record: dict) -> str:
    canonical = json.dumps(record, sort_keys=True, separators=(',',':'))
    payload = (prev_hash or "GENESIS") + canonical
    return hashlib.sha256(payload.encode()).hexdigest()
```

Tamper-evidence demo: change any field in any record → recomputing chain from that point fails to match downstream `hash_self` values.

---

## 6. Repository Structure

```
aegis-imaging/
├── backend/
│   ├── main.py
│   ├── orchestrator.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── intake.py
│   │   ├── forensics.py
│   │   ├── clinical.py
│   │   ├── verdict.py
│   │   └── audit.py
│   ├── ironlabs_router.py
│   ├── hf_detectors.py
│   ├── heatmap.py
│   ├── db.py
│   ├── webhooks.py
│   ├── schemas.py
│   └── tests/
│       ├── test_pipeline.py
│       └── fixtures/
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── pages/ (Upload, Verifying, Approved, Rejected, Escalated, Dashboard, AuditDetail)
│   │   ├── components/ (AgentCard, HeatmapViewer, VerdictBadge, MetricTile)
│   │   └── styles/
│   ├── tailwind.config.js
│   └── vite.config.ts
├── data/
│   ├── aegis.db
│   ├── uploads/
│   ├── heatmaps/
│   ├── synthetic_hash_db.json
│   ├── notifications.log
│   └── ironlabs_log.csv
├── demo/
│   ├── test_images/ (10 real + 10 AI-generated + 3 hero)
│   ├── demo_script.md
│   ├── slides.pdf
│   └── postman_collection.json
├── docker-compose.yml
├── .env.example
├── README.md
└── prds/ (all 6 PRD files)
```

---

## 7. Deployment & Runtime

### 7.1 Local Development

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### 7.2 Docker Compose (Demo Day Safety Net)

```yaml
version: "3.9"
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - IRONLABS_API_KEY=${IRONLABS_API_KEY}
      - IRONLABS_BASE_URL=${IRONLABS_BASE_URL}
      - HF_TOKEN=${HF_TOKEN}
    volumes:
      - ./data:/app/data
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on: [backend]
```

### 7.3 Environment Variables

```
IRONLABS_API_KEY=...
IRONLABS_BASE_URL=https://api.ironlabs.ai/v1
HF_TOKEN=...
DATABASE_URL=sqlite:///./data/aegis.db
DEMO_MODE=false   # set true to use cached verdicts as fallback
```

---

## 8. IronLabs Routing Matrix

| Agent | Task | Model Tier | Why |
|---|---|---|---|
| Intake | Metadata JSON extraction | Cheapest (Llama 8B) | Pure structure |
| Forensics | Vision artifact analysis | Mid + Vision (GPT-4o-mini) | Needs sight |
| Clinical | Anatomy plausibility | Mid + Vision (Claude Haiku Vision) | Needs domain reasoning |
| Verdict | Multi-source synthesis | Top reasoning (Claude Sonnet) | Critical decision |
| Audit | JSON formatting + sign | Cheapest (Llama 8B) | Pure templating |

**Fallback rule:** If a tier fails (timeout, 5xx), fall to next tier down. Verdict agent's fallback is "ESCALATE with rationale: model unavailable."

---

## 9. Performance Budget

| Stage | Budget (ms) | Notes |
|---|---|---|
| Image upload + hashing | 100 | Local I/O |
| Intake Agent | 300 | Llama 8B, ~200 tokens |
| Forensics Agent | 1200 | HF API + vision LLM in parallel |
| Clinical Agent | 1200 | Vision LLM |
| Verdict Agent | 500 | Sonnet text-only |
| Audit Agent | 100 | Llama 8B + DB write |
| Webhook delivery | 100 | Local fire-and-forget |
| **Total P50** | **~2000** | Agents 1–3 run in parallel; max ≈ 1200 |

---

## 10. Failure Modes & Degradation

| Failure | Behavior |
|---|---|
| HuggingFace timeout (10s) | Forensics returns partial result with `hf_failed: true` flag; verdict agent applies penalty |
| IronLabs 5xx | Fallback to next tier; if all fail → ESCALATE |
| One agent throws exception | Caught in orchestrator; verdict agent receives `{error: ...}` for that source |
| All agents fail | Orchestrator returns ESCALATE with rationale "verification system unavailable" |
| DB write fails | Verdict still returned to user; logged to file for manual recovery |

---

## 11. Security & Compliance Posture (Hackathon)

- No real PHI: all demo images are public-dataset or synthetic
- No authentication on demo build (mock-only)
- IronLabs and HF API keys in `.env`, never committed
- Image hashes (SHA-256) used as identifiers, never patient IDs
- Audit log designed to mirror HIPAA `45 CFR § 164.312(b)` requirements (audit controls)
- DPDP Act (India) alignment: data minimization, purpose limitation, retention policy stub in code

---

## 12. Architecture Decision Records (ADRs)

### ADR-001: Why SQLite, not Postgres
- Demo-only; single-file ship; zero ops; sufficient for <1000 records.

### ADR-002: Why 5 agents, not 1 big prompt
- Judges score "multi-agent" explicitly; specialization improves accuracy; parallel execution beats sequential latency; failure isolation.

### ADR-003: Why asyncio, not Celery
- Pipeline is sub-10s, no need for queueing; asyncio.gather gives free parallelism; one process keeps demo simple.

### ADR-004: Why vision-LLM bbox over true Grad-CAM
- True Grad-CAM requires model internals (not available via HF Inference API); LLM bbox is good enough for demo and looks identical to users.

### ADR-005: Why React + Vite, not Next.js
- No SSR needed; Vite dev server is faster; smaller surface area for bugs in 36 hours.
