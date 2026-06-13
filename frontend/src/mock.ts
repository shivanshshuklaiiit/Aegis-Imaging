// ─────────────────────────────────────────────────────────────────────────────
// Offline mock layer. Produces realistic verdicts and persists records in
// sessionStorage so result/audit/dashboard pages stay consistent across nav.
// ─────────────────────────────────────────────────────────────────────────────
import type { DashboardResponse, Verdict, VerifyResponse } from "./api";

const STORE_KEY = "aegis_mock_records";

function loadStore(): Record<string, VerifyResponse> {
  try {
    return JSON.parse(sessionStorage.getItem(STORE_KEY) || "{}");
  } catch {
    return {};
  }
}

function saveStore(s: Record<string, VerifyResponse>) {
  sessionStorage.setItem(STORE_KEY, JSON.stringify(s));
}

function nextAuditId(): string {
  const d = new Date();
  const ymd = `${d.getFullYear()}${String(d.getMonth() + 1).padStart(2, "0")}${String(
    d.getDate()
  ).padStart(2, "0")}`;
  const n = String(Math.floor(Math.random() * 90000) + 1000).padStart(5, "0");
  return `AEG-${ymd}-${n}`;
}

function sha(len = 64): string {
  const hex = "0123456789abcdef";
  let s = "";
  for (let i = 0; i < len; i++) s += hex[Math.floor(Math.random() * 16)];
  return s;
}

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => resolve("");
    reader.readAsDataURL(file);
  });
}

// Deterministic-ish verdict so demos are repeatable by filename keyword.
function pickVerdict(filename: string): Verdict {
  const f = filename.toLowerCase();
  if (/(fake|ai|gen|synthetic|tamper|reject)/.test(f)) return "REJECT";
  if (/(ambig|escal|unclear|old|film|uncertain)/.test(f)) return "ESCALATE";
  if (/(real|approve|genuine|clean)/.test(f)) return "APPROVE";
  // default: weighted random favouring APPROVE
  const r = Math.random();
  return r < 0.6 ? "APPROVE" : r < 0.85 ? "REJECT" : "ESCALATE";
}

function buildResponse(
  verdict: Verdict,
  modality: string,
  imageDataUrl: string
): VerifyResponse {
  const audit_id = nextAuditId();
  const latency = 1200 + Math.floor(Math.random() * 2200);
  const cost = +(0.0018 + Math.random() * 0.004).toFixed(4);

  const profiles: Record<Verdict, () => Omit<VerifyResponse, "audit_id" | "modality" | "image_url" | "created_at" | "total_latency_ms" | "total_cost_usd" | "hash_chain">> = {
    REJECT: () => ({
      verdict: "REJECT",
      confidence: 0.88 + Math.random() * 0.09,
      rationale:
        "Image exhibits characteristic SDXL frequency artifacts and anatomically implausible bone texture. Forensics and clinical agents agree this is synthetically generated.",
      evidence: [
        { type: "frequency_artifact", region: [120, 80, 200, 180], score: 0.87, source_agent: "forensics" },
        { type: "texture_inconsistency", region: [240, 150, 320, 260], score: 0.81, source_agent: "forensics" },
        { type: "implausible_anatomy", region: [90, 200, 180, 300], score: 0.76, source_agent: "clinical" },
      ],
      heatmap_url: imageDataUrl || null,
      agent_outputs: {
        intake: { score: 0.3, metadata_complete: false, anomalies: ["missing_dicom_tags", "uniform_noise_floor"] },
        forensics: { score: 0.87, ai_probability: 0.92, detector: "sdxl-detector-v2" },
        clinical: { score: 0.82, plausibility: 0.18, notes: "Rib spacing inconsistent with stated modality" },
        verdict: { score: 0.91, weighted_total: 0.83, decision: "REJECT" },
      },
    }),
    ESCALATE: () => ({
      verdict: "ESCALATE",
      confidence: 0.55 + Math.random() * 0.12,
      rationale:
        "Forensics agent reports high uncertainty due to low scan quality. Evidence is inconclusive — routing to a human reviewer for final determination.",
      evidence: [
        { type: "low_quality_scan", region: [60, 60, 260, 260], score: 0.52, source_agent: "intake" },
        { type: "ambiguous_artifact", region: [150, 120, 230, 210], score: 0.49, source_agent: "forensics" },
      ],
      heatmap_url: imageDataUrl || null,
      agent_outputs: {
        intake: { score: 0.5, metadata_complete: false, anomalies: ["low_resolution"] },
        forensics: { score: 0.48, ai_probability: 0.51, hf_failed: false },
        clinical: { score: 0.55, plausibility: 0.58 },
        verdict: { score: 0.55, weighted_total: 0.52, decision: "ESCALATE" },
      },
    }),
    APPROVE: () => ({
      verdict: "APPROVE",
      confidence: 0.9 + Math.random() * 0.08,
      rationale:
        "All agents concur the image is authentic. Metadata is complete, no generative artifacts detected, and anatomy is clinically plausible for the stated modality.",
      evidence: [],
      heatmap_url: null,
      agent_outputs: {
        intake: { score: 0.94, metadata_complete: true, anomalies: [] },
        forensics: { score: 0.05, ai_probability: 0.04, detector: "sdxl-detector-v2" },
        clinical: { score: 0.93, plausibility: 0.95 },
        verdict: { score: 0.94, weighted_total: 0.93, decision: "APPROVE" },
      },
    }),
  };

  const base = profiles[verdict]();
  return {
    audit_id,
    ...base,
    confidence: +base.confidence.toFixed(2),
    image_url: imageDataUrl || null,
    modality,
    created_at: new Date().toISOString(),
    total_latency_ms: latency,
    total_cost_usd: cost,
    hash_chain: { prev: sha(), self: sha() },
  };
}

export async function mockVerify(file: File, modality: string): Promise<VerifyResponse> {
  const dataUrl = await fileToDataUrl(file);
  const verdict = pickVerdict(file.name);
  const res = buildResponse(verdict, modality, dataUrl);
  const store = loadStore();
  store[res.audit_id] = res;
  saveStore(store);
  // simulate pipeline latency
  await new Promise((r) => setTimeout(r, 400));
  return res;
}

export async function mockAudit(id: string): Promise<VerifyResponse> {
  const store = loadStore();
  if (store[id]) return store[id];
  // Synthesize a record if not in session (e.g. clicked a seeded dashboard row).
  const v: Verdict = id.endsWith("1") ? "REJECT" : id.endsWith("2") ? "ESCALATE" : "APPROVE";
  return buildResponse(v, "xray", "");
}

export async function mockDashboard(): Promise<DashboardResponse> {
  const store = loadStore();
  const session = Object.values(store);

  const seeded = SEED_AUDITS;
  const all = [...session, ...seeded.map(seedToResp)];

  const count = (v: Verdict) => all.filter((a) => a.verdict === v).length;
  const totalCost = all.reduce((s, a) => s + a.total_cost_usd, 0);

  return {
    totals: {
      verifications_today: all.length,
      approve: count("APPROVE"),
      reject: count("REJECT"),
      escalate: count("ESCALATE"),
    },
    latency: { p50_ms: 1840, p95_ms: 3200 },
    cost: {
      total_usd: +totalCost.toFixed(3),
      by_model: {
        "llama-3.1-8b-instruct": 0.018,
        "gpt-4o-mini": 0.084,
        "claude-haiku-vision": 0.031,
        "claude-sonnet": 0.052,
      },
      saved_vs_top_tier_usd: 0.31,
      saved_percent: 68.6,
    },
    recent_audits: all
      .sort((a, b) => (b.created_at || "").localeCompare(a.created_at || ""))
      .slice(0, 12)
      .map((a) => ({
        audit_id: a.audit_id,
        verdict: a.verdict,
        confidence: a.confidence,
        modality: a.modality,
        total_latency_ms: a.total_latency_ms,
        total_cost_usd: a.total_cost_usd,
        created_at: a.created_at || new Date().toISOString(),
      })),
  };
}

// ── Seed data so the dashboard never looks empty during a demo ───────────────
interface Seed {
  audit_id: string;
  verdict: Verdict;
  confidence: number;
  modality: string;
  total_latency_ms: number;
  total_cost_usd: number;
  minsAgo: number;
}

const SEED_AUDITS: Seed[] = [
  { audit_id: "AEG-20260613-00042", verdict: "REJECT", confidence: 0.91, modality: "xray", total_latency_ms: 1840, total_cost_usd: 0.0031, minsAgo: 4 },
  { audit_id: "AEG-20260613-00041", verdict: "APPROVE", confidence: 0.94, modality: "xray", total_latency_ms: 1620, total_cost_usd: 0.0026, minsAgo: 9 },
  { audit_id: "AEG-20260613-00040", verdict: "APPROVE", confidence: 0.96, modality: "mri", total_latency_ms: 2100, total_cost_usd: 0.0038, minsAgo: 15 },
  { audit_id: "AEG-20260613-00039", verdict: "ESCALATE", confidence: 0.58, modality: "ct", total_latency_ms: 3010, total_cost_usd: 0.0041, minsAgo: 22 },
  { audit_id: "AEG-20260613-00038", verdict: "APPROVE", confidence: 0.92, modality: "ultrasound", total_latency_ms: 1490, total_cost_usd: 0.0022, minsAgo: 31 },
  { audit_id: "AEG-20260613-00037", verdict: "REJECT", confidence: 0.89, modality: "xray", total_latency_ms: 1980, total_cost_usd: 0.0034, minsAgo: 44 },
  { audit_id: "AEG-20260613-00036", verdict: "APPROVE", confidence: 0.93, modality: "mri", total_latency_ms: 2240, total_cost_usd: 0.0039, minsAgo: 58 },
];

function seedToResp(s: Seed): VerifyResponse {
  return {
    audit_id: s.audit_id,
    verdict: s.verdict,
    confidence: s.confidence,
    rationale: "",
    evidence: [],
    heatmap_url: null,
    image_url: null,
    modality: s.modality,
    created_at: new Date(Date.now() - s.minsAgo * 60000).toISOString(),
    agent_outputs: {},
    total_latency_ms: s.total_latency_ms,
    total_cost_usd: s.total_cost_usd,
    hash_chain: { prev: sha(), self: sha() },
  };
}
