// ─────────────────────────────────────────────────────────────────────────────
// Aegis API client. Typed fetch wrappers with graceful mock fallback so the UI
// works fully offline (demo safety net) and the instant the backend is up.
// ─────────────────────────────────────────────────────────────────────────────
import {
  mockVerify,
  mockDashboard,
  mockAudit,
} from "./mock";

const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

// VITE_MOCK="true" forces mock, "false" forbids it. Unset = auto-fallback on error.
const MOCK_FLAG = (import.meta.env.VITE_MOCK ?? "").toString().toLowerCase();
export const FORCE_MOCK = MOCK_FLAG === "true";
const FORBID_MOCK = MOCK_FLAG === "false";

export type Verdict = "APPROVE" | "REJECT" | "ESCALATE";

export interface Evidence {
  type: string;
  region?: number[];
  score: number;
  source_agent: string;
}

export interface VerifyResponse {
  audit_id: string;
  verdict: Verdict;
  confidence: number;
  rationale: string;
  evidence: Evidence[];
  heatmap_url: string | null;
  image_url?: string | null;
  modality?: string;
  created_at?: string;
  agent_outputs: Record<string, any>;
  total_latency_ms: number;
  total_cost_usd: number;
  hash_chain: { prev: string; self: string };
}

export interface DashboardResponse {
  totals: {
    verifications_today: number;
    approve: number;
    reject: number;
    escalate: number;
  };
  latency: { p50_ms: number; p95_ms: number };
  cost: {
    total_usd: number;
    by_model: Record<string, number>;
    saved_vs_top_tier_usd: number;
    saved_percent: number;
  };
  recent_audits: Array<{
    audit_id: string;
    verdict: Verdict;
    confidence: number;
    modality?: string;
    total_latency_ms: number;
    total_cost_usd: number;
    created_at: string;
  }>;
}

/** Resolve an absolute URL for backend-served static assets (heatmaps/images). */
export function assetUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith("http") || path.startsWith("data:") || path.startsWith("blob:")) return path;
  return `${BASE}${path}`;
}

function maybeMock<T>(make: () => T): T {
  if (FORBID_MOCK) throw new Error("Backend unavailable and mock mode disabled.");
  return make();
}

export async function verifyImage(
  file: File,
  modality: string
): Promise<VerifyResponse> {
  if (FORCE_MOCK) return mockVerify(file, modality);
  try {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("modality", modality);
    const r = await fetch(`${BASE}/api/v1/verify`, { method: "POST", body: fd });
    if (!r.ok) throw new Error(`Verify failed: ${r.status}`);
    return await r.json();
  } catch (e) {
    return maybeMock(() => mockVerify(file, modality));
  }
}

export async function getDashboard(): Promise<DashboardResponse> {
  if (FORCE_MOCK) return mockDashboard();
  try {
    const r = await fetch(`${BASE}/api/v1/dashboard`);
    if (!r.ok) throw new Error(`Dashboard failed: ${r.status}`);
    return await r.json();
  } catch (e) {
    return maybeMock(() => mockDashboard());
  }
}

export async function getAudit(id: string): Promise<VerifyResponse> {
  if (FORCE_MOCK) return mockAudit(id);
  try {
    const r = await fetch(`${BASE}/api/v1/audit/${id}`);
    if (!r.ok) throw new Error(`Audit fetch failed: ${r.status}`);
    return await r.json();
  } catch (e) {
    return maybeMock(() => mockAudit(id));
  }
}
