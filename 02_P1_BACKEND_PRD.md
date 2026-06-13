# P1 — Backend Lead PRD (Shiv)

**Role:** Agent Architect
**Owner:** Shiv
**Reports to:** Self (team lead) + team consensus on contracts

---

## 1. Mission

Own the backend brain of Aegis Imaging end-to-end: FastAPI service, async orchestrator, three of the five agents (Intake, Verdict, Audit), the IronLabs router, and all backend integration points. Be the technical anchor — when integration breaks at H16, you debug it.

---

## 2. Deliverables

| # | Deliverable | Definition of Done |
|---|---|---|
| D1 | FastAPI scaffold with routes | `/api/v1/verify`, `/audit/{id}`, `/dashboard` return shapes match Architecture PRD §4 |
| D2 | `IronLabsRouter` class | Maps task_type → model, logs every call to `ironlabs_log.csv` and DB, has fallback chain |
| D3 | `AsyncOrchestrator` | Runs agents 1–3 in parallel (asyncio.gather), then 4, then 5; total <10s hard timeout |
| D4 | Intake Agent | Extracts DICOM/EXIF metadata, computes pHash, checks synthetic hash DB, returns triage score |
| D5 | Verdict Agent | Weighted ensemble: 0.2·intake + 0.5·forensics + 0.3·clinical → APPROVE/REJECT/ESCALATE |
| D6 | Audit Agent | Writes verification record with SHA-256 hash chain link; triggers webhooks |
| D7 | SQLite DB layer | Schema applied on startup; `verifications`, `ironlabs_calls`, `mock_ehr_events` tables |
| D8 | Pydantic schemas | All request/response shapes validated; no `dict[str, Any]` in public API |
| D9 | Error handling | Each agent wrapped in try/except; orchestrator never crashes; failures degrade to ESCALATE |
| D10 | Integration: receive P2's agents | Agents 2 and 3 plug in via the `BaseAgent` interface without orchestrator changes |

---

## 3. Hour-by-Hour Plan

### Sprint 1: Foundation (H0–H2)

- Initialize repo, push to GitHub
- Create folder structure per Architecture PRD §6
- Pin Python version, write `requirements.txt`
- **At H2 sync: lock API contract with P3** — exact JSON shapes for `/verify`, `/audit/{id}`, `/dashboard`
- **At H2 sync: lock `BaseAgent` interface with P2** — what context dict looks like, what every agent must return

### Sprint 2: Plumbing (H2–H8)

- Implement `db.py` — schema creation, hash chain function, helper queries
- Implement `ironlabs_router.py` — full version with logging and fallback
- Implement `BaseAgent` abstract class
- Implement Intake Agent (working with real DICOM and PNG/JPEG)
- Implement Verdict Agent (with stubbed forensics/clinical outputs for now)
- Wire `/verify` route end-to-end with stubs returning fake APPROVE
- **At H8 sync: integration test with P3's frontend** — upload an image, get a verdict, render result

### Sprint 3: Real Agents (H8–H16)

- Pair with P2 — wire Forensics and Clinical agents into orchestrator
- Implement asyncio.gather for parallel execution of agents 1–3
- Implement timeout handling (10s hard cap on full pipeline)
- Implement fallback logic in IronLabsRouter
- **At H16 sync: end-to-end real test** with one image, one real verdict — this will break, leave buffer

### Sprint 4: Audit & Webhooks (H16–H22)

- Implement Audit Agent with hash chain
- Implement webhook posting (P4 owns the endpoints; you call them)
- Build `/audit/{id}` route
- Build `/dashboard` route with real metrics from DB

### Sprint 5: Hardening (H22–H30)

- Run P2's 20-image test suite, fix accuracy issues by adjusting Verdict weights
- Add request validation, file size limits, content-type checks
- Optimize latency — find any sequential calls that can parallelize
- Add `DEMO_MODE` env var that serves cached verdicts as backup

### Sprint 6: Demo Support (H30–H36)

- Be present at every dry-run
- Fix whatever breaks
- Help P4 rehearse demo
- Sleep 4 hours before final demo

---

## 4. Code Skeletons (Start Here)

### 4.1 `agents/base.py`

```python
from abc import ABC, abstractmethod
from typing import Any
import time

class BaseAgent(ABC):
    name: str = "base"

    async def execute(self, context: dict) -> dict:
        start = time.time()
        try:
            result = await self.run(context)
            result["agent"] = self.name
            result["latency_ms"] = int((time.time() - start) * 1000)
            result["error"] = None
        except Exception as e:
            result = {
                "agent": self.name,
                "score": 0.0,
                "evidence": [],
                "latency_ms": int((time.time() - start) * 1000),
                "error": str(e),
            }
        return result

    @abstractmethod
    async def run(self, context: dict) -> dict:
        ...
```

### 4.2 `orchestrator.py`

```python
import asyncio
from agents.intake import IntakeAgent
from agents.forensics import ForensicsAgent
from agents.clinical import ClinicalAgent
from agents.verdict import VerdictAgent
from agents.audit import AuditAgent

PIPELINE_TIMEOUT_SEC = 10

class AsyncOrchestrator:
    def __init__(self):
        self.intake = IntakeAgent()
        self.forensics = ForensicsAgent()
        self.clinical = ClinicalAgent()
        self.verdict = VerdictAgent()
        self.audit = AuditAgent()

    async def run(self, context: dict) -> dict:
        async def pipeline():
            # Stage 1: parallel agents
            intake_r, forensics_r, clinical_r = await asyncio.gather(
                self.intake.execute(context),
                self.forensics.execute(context),
                self.clinical.execute(context),
                return_exceptions=False,
            )
            context["intake"] = intake_r
            context["forensics"] = forensics_r
            context["clinical"] = clinical_r

            # Stage 2: verdict
            verdict_r = await self.verdict.execute(context)
            context["verdict"] = verdict_r

            # Stage 3: audit
            audit_r = await self.audit.execute(context)
            context["audit"] = audit_r

            return context

        try:
            return await asyncio.wait_for(pipeline(), timeout=PIPELINE_TIMEOUT_SEC)
        except asyncio.TimeoutError:
            return self._timeout_response(context)

    def _timeout_response(self, context):
        return {
            "verdict": "ESCALATE",
            "confidence": 0.5,
            "rationale": "Verification pipeline timed out; human review required.",
            "error": "timeout",
        }
```

### 4.3 `agents/verdict.py`

```python
from agents.base import BaseAgent
from ironlabs_router import IronLabsRouter
import json

WEIGHTS = {"intake": 0.2, "forensics": 0.5, "clinical": 0.3}
APPROVE_THRESHOLD = 0.75
REJECT_THRESHOLD  = 0.35

class VerdictAgent(BaseAgent):
    name = "verdict"

    def __init__(self):
        self.router = IronLabsRouter()

    async def run(self, context: dict) -> dict:
        scores = {
            k: context[k].get("score", 0.5) for k in ("intake","forensics","clinical")
        }
        # "score" here is "trust score" — higher = more likely genuine
        weighted = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)

        if weighted >= APPROVE_THRESHOLD:
            decision = "APPROVE"
        elif weighted <= REJECT_THRESHOLD:
            decision = "REJECT"
        else:
            decision = "ESCALATE"

        # Use top-tier LLM to write the rationale
        prompt = self._build_prompt(context, decision, weighted)
        rationale = self.router.route("critical_decision", prompt)

        return {
            "score": weighted,
            "decision": decision,
            "confidence": weighted if decision != "ESCALATE" else 0.5,
            "rationale": rationale,
            "weighted_total": weighted,
            "component_scores": scores,
        }

    def _build_prompt(self, ctx, decision, weighted):
        return f"""You are the Chief Verification Officer for Aegis Imaging.

Three specialist agents reported on a medical image:
- Intake/Metadata: {json.dumps(ctx['intake'])}
- Visual Forensics: {json.dumps(ctx['forensics'])}
- Clinical Plausibility: {json.dumps(ctx['clinical'])}

Weighted trust score: {weighted:.2f}
Decision: {decision}

Write a 2-3 sentence human-readable rationale for this decision in the voice of a
clinical compliance officer. Be specific about evidence. Do not include preamble."""
```

### 4.4 `ironlabs_router.py`

See Master Blueprint section 6. Add:
- Try/except around `client.chat.completions.create`
- Fallback chain: top → mid → cheap → static fallback string
- DB write to `ironlabs_calls` table on every call

---

## 5. Interfaces You Own

### To P2 (ML Engineer)
- You give: `BaseAgent` interface and `IronLabsRouter` instance
- They give: working `ForensicsAgent` and `ClinicalAgent` classes implementing `BaseAgent`

### To P3 (Frontend)
- You give: API contract (JSON shapes, status codes, error formats)
- They give: nothing back to you, but they'll file integration bugs in #aegis-bugs

### To P4 (Product)
- You give: webhook trigger calls + access to DB for dashboard data
- They give: `/mock-ehr` and `/mock-claims` endpoint specs

---

## 6. Success Criteria

By H30 you must have:
- ✅ `curl -X POST -F "file=@chest.png" -F "modality=xray" localhost:8000/api/v1/verify` returns a valid verdict in <3s
- ✅ Every verdict creates a row in `verifications` table with valid hash chain
- ✅ Every LLM call creates a row in `ironlabs_calls` with cost and latency
- ✅ Webhook fires on every verdict and is logged
- ✅ `/dashboard` returns real numbers, not stubs
- ✅ Pipeline survives at least one agent failing
- ✅ All Pydantic schemas validate; no 500 errors on bad input

---

## 7. Things That Will Bite You

1. **DICOM files are weird.** Some have no PixelData, some have weird transfer syntax. Have a try/except around pydicom and fall back to "metadata_missing".
2. **HuggingFace cold starts can be 30s.** Either pre-warm at startup or call HF API and cache the first response.
3. **IronLabs SDK may not be exactly OpenAI-compatible.** Spend the first 30 min in the docs. If it has a Python SDK, prefer that over the OpenAI wrapper.
4. **asyncio.gather raises on first exception.** Use `return_exceptions=True` if you want partial results, then check each result for `Exception` instance.
5. **SQLite is single-writer.** Use `aiosqlite` or wrap writes in a thread executor to avoid blocking the event loop.
6. **Hash chain breaks if you re-order JSON keys.** Always use `json.dumps(..., sort_keys=True)`.

---

## 8. Daily Standups

- **H0:** Kickoff sync, contracts agreed
- **H8:** Foundation check — can a fake verdict round-trip?
- **H16:** Real integration day — expect chaos, leave buffer
- **H24:** Polish day — accuracy tuning with P2
- **H32:** Demo prep — be on standby
