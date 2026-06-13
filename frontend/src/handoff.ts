// In-memory handoff for the pending upload (File objects aren't reliably
// serializable into router/history state, so we stash them here).
import type { VerifyResponse } from "./api";

interface Pending {
  file: File;
  modality: string;
  previewUrl: string;
}

let pending: Pending | null = null;
const results = new Map<string, VerifyResponse>();

export function setPending(p: Pending) {
  pending = p;
}
export function takePending(): Pending | null {
  const p = pending;
  return p;
}
export function clearPending() {
  pending = null;
}

export function cacheResult(r: VerifyResponse) {
  results.set(r.audit_id, r);
}
export function getCachedResult(id: string): VerifyResponse | undefined {
  return results.get(id);
}
