import { useEffect, useState } from "react";
import { getAudit, type VerifyResponse } from "./api";
import { getCachedResult } from "./handoff";

// Loads a verification result by audit id: in-memory cache first (fresh from the
// verifying flow), then falls back to the audit endpoint (mock or real).
export function useResult(id: string | undefined) {
  const [data, setData] = useState<VerifyResponse | null>(
    id ? getCachedResult(id) ?? null : null
  );
  const [loading, setLoading] = useState(!data);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id || data) return;
    let live = true;
    setLoading(true);
    getAudit(id)
      .then((r) => live && setData(r))
      .catch((e) => live && setError(String(e)))
      .finally(() => live && setLoading(false));
    return () => {
      live = false;
    };
  }, [id, data]);

  return { data, loading, error };
}
