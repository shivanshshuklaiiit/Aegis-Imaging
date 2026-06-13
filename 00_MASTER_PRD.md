# Aegis Imaging — Master PRD

**Version:** 1.0
**Date:** June 13, 2026
**Owners:** Shiv (P1), P2, P3, P4
**Hackathon:** IronLabs AI Hackathon, Delhi NCR
**Status:** Active — Implementation begins H0

---

## 1. Product Vision

**Aegis Imaging is the agentic trust layer for medical imaging.**

Every X-ray, MRI, CT, and ultrasound that enters a hospital, insurance claim, or telemedicine workflow is verified by a panel of specialized AI agents before it can influence a clinical or financial decision. We detect AI-generated, deepfaked, and tampered medical images in under 2 seconds, with a cryptographically auditable trail.

**Tagline:** *Every scan, verified.*

---

## 2. Problem Statement

Three converging trends create a critical vulnerability in healthcare:

1. **Generative AI is now trivial.** SDXL, Midjourney, and open-source diffusion models can produce convincing medical images in seconds, at zero marginal cost.
2. **Healthcare workflows assume image authenticity.** PACS systems, claims processors, and EHRs have no built-in verification — they treat every uploaded image as genuine.
3. **The attack surface is enormous.** Indian healthcare loses an estimated ₹45,000 crore annually to insurance fraud. Globally, telemedicine, clinical trials, and tele-radiology all rely on image-based decision-making with no integrity check.

**Concrete threat scenarios:**
- A fraudster generates a fake X-ray showing a fracture, submits to insurance for ₹2L payout
- A trial participant uploads AI-generated MRIs to qualify for paid clinical trials
- A bad actor manipulates radiology images to extract controlled substance prescriptions
- A nation-state seeds synthetic imagery into a hospital's training data

---

## 3. Target Users & Personas

| Persona | Role | Primary Need | Buys Because |
|---|---|---|---|
| **Priya — Claims Processor** | Insurance | Verify 200+ claim images/day | Fraud prevention ROI |
| **Dr. Arjun — Radiologist** | Hospital | Trust incoming teleradiology scans | Liability protection |
| **Meera — Compliance Officer** | Hospital chain | Defensible audit trail per scan | HIPAA/DPDP compliance |
| **Vikram — CTO** | Telemedicine startup | API integration before scale | Brand risk mitigation |

**Primary buyer (v1):** Insurance claims teams. Highest ROI, clearest fraud signal, lowest integration complexity.

---

## 4. Goals & Success Metrics

### Hackathon Demo Success Criteria

| Metric | Target | Stretch |
|---|---|---|
| Detection accuracy (20-image test set) | ≥85% | ≥92% |
| P50 verification latency | <2.5s | <1.8s |
| P95 verification latency | <5s | <3.5s |
| Cost per verification | <$0.01 | <$0.005 |
| Agents working in production demo | 4 of 5 | 5 of 5 |
| Successful demo runs without crash | 1 (the real one) | 3 dry-runs + 1 real |
| Audit records with valid hash chain | 100% | 100% |
| Mock EHR webhook deliveries | Functional | Two integrations (EHR + claims) |

### Post-Hackathon (V2) Success Criteria

- 1 paid pilot with an Indian hospital chain or insurer
- ≥95% accuracy on 1,000-image curated test set
- <1s P50 latency at 100 RPS
- SOC2 Type 1 within 9 months

---

## 5. Scope

### In Scope (Hackathon MVP)

- Upload PNG, JPEG, or DICOM files up to 20MB
- 5-agent verification pipeline (Intake, Forensics, Clinical, Verdict, Audit)
- Three-way verdict: APPROVE, REJECT, ESCALATE
- Confidence score and human-readable rationale
- Heatmap overlay highlighting suspicious regions
- Cryptographically chained audit log (SHA-256)
- Mock EHR webhook (`/mock-ehr`) and claims webhook (`/mock-claims`)
- Cost and latency dashboard with IronLabs routing breakdown
- REST API for programmatic use (curl one-liner demo)
- Audit detail page with full agent JSON breakdown

### Out of Scope (V1)

- Real PACS or DICOM-network integration
- Real PHI storage or HIPAA-compliant infrastructure
- Multi-tenancy / organization accounts
- Model retraining UI
- User authentication beyond a mock login
- Mobile native apps
- Real-time stream processing (only file uploads)

---

## 6. User Journeys

### Journey A — Insurance Claims Processor (Reject Path)
1. Priya receives a claim with a fracture X-ray attached
2. She uploads it to Aegis via her claims platform's "Verify" button (mock integration)
3. Aegis returns `REJECT` in 1.8s with heatmap showing AI-generated artifacts
4. Claims platform auto-flags the claim for fraud review
5. Audit record is delivered to compliance system with hash chain

### Journey B — Teleradiologist (Approve Path)
1. Dr. Arjun's reading queue receives a chest X-ray from a partner hospital
2. PACS-like UI calls Aegis before opening the image
3. Aegis returns `APPROVE` with 0.94 confidence
4. Image opens normally in Dr. Arjun's viewer
5. Audit trail attached to the diagnostic report

### Journey C — Compliance Officer (Audit Path)
1. Meera receives a regulatory audit request: "show us your fraud prevention controls"
2. She opens the Aegis dashboard
3. She filters by date range and exports the audit log
4. Each record shows: image hash, all agent outputs, verdict, model versions, hash-chain link
5. She demonstrates tamper-evidence by recomputing the chain

### Journey D — Edge Case (Escalate Path)
1. An ambiguous image is uploaded — old film X-ray with poor scan quality
2. Forensics agent reports high uncertainty
3. Verdict agent issues `ESCALATE` with rationale
4. UI shows amber banner with "Forward to Human Reviewer" button
5. Mock notification sent to a "reviewer" inbox

---

## 7. Functional Requirements

### FR-1 — Image Upload
- Accept PNG, JPEG, DICOM (.dcm) up to 20MB
- Reject other formats with clear error
- Compute SHA-256 of file on upload
- Store original in `/data/uploads/{sha256}.{ext}`

### FR-2 — Multi-Agent Pipeline
- 5 agents execute per verification
- Agents 1, 2, 3 run in parallel (asyncio.gather)
- Agent 4 runs after 1-3 complete
- Agent 5 runs after Agent 4
- Total pipeline must complete in <10s hard timeout

### FR-3 — Verdict Output
- One of: APPROVE, REJECT, ESCALATE
- Confidence score 0.0–1.0
- Rationale: 1–3 sentence human-readable explanation
- Evidence array with type, region (bbox), and individual score
- Heatmap PNG URL if any suspicious regions identified

### FR-4 — Audit Trail
- Every verification produces an audit record
- Records are immutable once written
- Each record contains SHA-256 hash of itself and link to previous record's hash
- Audit ID format: `AEG-YYYYMMDD-NNNNN`

### FR-5 — IronLabs Routing
- All LLM calls go through a single `IronLabsRouter` class
- Router maps task complexity → model tier
- Each call logged with model, tokens, cost, latency
- Fallback to next tier on failure

### FR-6 — Mock Integrations
- `POST /mock-ehr` accepts FHIR-lite payload, logs to file
- `POST /mock-claims` accepts claims-platform payload, logs to file
- Triggered automatically by Audit Agent on every verdict

### FR-7 — Dashboard
- Live metrics: total verifications, verdict breakdown, avg latency, total cost saved
- IronLabs routing chart: cost per model tier
- Audit log table with filtering
- Per-record drilldown to full agent JSON

### FR-8 — Public API
- `POST /api/v1/verify` with multipart image upload
- Returns full verdict JSON
- Demoable with single curl command

---

## 8. Non-Functional Requirements

| Category | Requirement |
|---|---|
| **Latency** | P50 <2.5s, P95 <5s, hard timeout 10s |
| **Reliability** | Pipeline completes even if 1 agent fails (graceful degrade to ESCALATE) |
| **Cost** | Per-verification LLM cost <$0.01 average |
| **Security** | No PHI in logs; image hashes only; mock auth acceptable |
| **Auditability** | 100% of verdicts written to audit DB with hash chain |
| **Observability** | Per-call IronLabs CSV log; dashboard reflects real numbers |
| **Portability** | Runs locally with `docker-compose up` |

---

## 9. Tech Stack (Locked)

- **Backend:** Python 3.11+, FastAPI, asyncio, Pydantic, SQLite
- **Frontend:** React 18 + Vite + TypeScript + Tailwind CSS + recharts
- **ML:** HuggingFace Inference API, OpenCV, Pillow, pydicom, imagehash
- **LLM routing:** IronLabs (OpenAI-compatible API)
- **DB:** SQLite (single file, demo-friendly)
- **Deployment:** Local + Docker Compose (no cloud dependency for demo)
- **Dev tools:** Emergent (initial scaffold), GitHub, Postman

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| HuggingFace inference timeouts during demo | Medium | High | Pre-warm models at H30; cache 20 demo verdicts as fallback |
| IronLabs API quota exhausted | Low | High | Use cheapest tier for 80% of calls; have OpenAI key as backup |
| Live Wi-Fi fails at venue | Medium | Critical | Pre-record full demo video; have ngrok backup tunnel |
| One agent breaks in integration | High | Medium | Each agent independently testable; orchestrator gracefully degrades |
| Demo image classified wrong on stage | Medium | High | Curate 20 images, test all, hand-pick 3 hero images that always work |
| Team member sick / drops | Medium | High | Documented backup plan in Team Split doc |
| Slides not ready by demo | Low | High | P4 finishes slide v1 by H16, polishes after |

---

## 11. Open Questions

- [ ] Confirm IronLabs exact model names and pricing (resolve H0)
- [ ] Confirm hackathon submission format (Devpost? video? live?) — P4 to verify
- [ ] Will judges have technical depth? Adjust pitch tone accordingly
- [ ] Is there a sponsor track prize for IronLabs we should target?

---

## 12. References

- See `01_ARCHITECTURE_PRD.md` for system design
- See `02_P1_BACKEND_PRD.md` for Shiv's deliverables
- See `03_P2_ML_PRD.md` for detection lead deliverables
- See `04_P3_FRONTEND_PRD.md` for UI lead deliverables
- See `05_P4_PRODUCT_PRD.md` for pitch/integrations lead deliverables
