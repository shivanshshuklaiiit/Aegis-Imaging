import { useState } from "react";
import type { Evidence } from "../api";

// Renders the image with a forensic heatmap overlay. When a real heatmap PNG is
// provided we layer it; otherwise we synthesize region highlights from evidence
// bboxes so the "suspicious zones" read clearly even in offline/mock mode.
export default function HeatmapViewer({
  imageUrl,
  heatmapUrl,
  evidence = [],
  showOverlayDefault = true,
}: {
  imageUrl: string | null;
  heatmapUrl: string | null;
  evidence?: Evidence[];
  showOverlayDefault?: boolean;
}) {
  const [showOverlay, setShowOverlay] = useState(showOverlayDefault);
  const src = imageUrl || heatmapUrl;

  return (
    <div className="space-y-3">
      <div className="relative overflow-hidden rounded-lg border border-aegis-border bg-aegis-navy/5">
        {src ? (
          <img src={src} alt="Scan under verification" className="block max-h-[420px] w-full object-contain" />
        ) : (
          <div className="flex h-64 items-center justify-center text-sm text-aegis-slate">
            Image preview unavailable
          </div>
        )}

        {showOverlay && (
          <div className="pointer-events-none absolute inset-0">
            {/* Real heatmap layer if backend produced a distinct PNG */}
            {heatmapUrl && heatmapUrl !== imageUrl && (
              <img src={heatmapUrl} alt="" className="absolute inset-0 h-full w-full object-contain opacity-60 mix-blend-multiply" />
            )}
            {/* Synthetic region highlights from evidence bboxes (percent-based) */}
            {evidence
              .filter((e) => e.region && e.region.length === 4)
              .map((e, i) => {
                const [x, y, x2, y2] = e.region as number[];
                // bboxes are in a nominal 0..384 space; clamp to a sane percentage
                const N = 384;
                const left = Math.min(x, x2) / N;
                const top = Math.min(y, y2) / N;
                const w = Math.abs(x2 - x) / N;
                const h = Math.abs(y2 - y) / N;
                return (
                  <div
                    key={i}
                    className="absolute rounded animate-pulse-ring"
                    style={{
                      left: `${left * 100}%`,
                      top: `${top * 100}%`,
                      width: `${w * 100}%`,
                      height: `${h * 100}%`,
                      boxShadow: "0 0 0 2px rgba(220,38,38,0.9), 0 0 40px 8px rgba(220,38,38,0.45) inset",
                      background:
                        "radial-gradient(ellipse at center, rgba(220,38,38,0.45), rgba(220,38,38,0.08) 70%)",
                    }}
                  />
                );
              })}
          </div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs text-aegis-slate">
          {evidence.length > 0
            ? `${evidence.length} suspicious region${evidence.length > 1 ? "s" : ""} highlighted`
            : "No suspicious regions"}
        </span>
        <button onClick={() => setShowOverlay((v) => !v)} className="text-xs font-medium text-aegis-blue hover:underline">
          {showOverlay ? "Hide heatmap" : "Show heatmap"}
        </button>
      </div>
    </div>
  );
}
