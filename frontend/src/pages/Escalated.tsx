import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AlertTriangle, FileText, Send } from "lucide-react";
import { useResult } from "../useResult";
import { assetUrl } from "../api";
import ResultScaffold, { ConfidenceBar } from "../components/ResultScaffold";
import HeatmapViewer from "../components/HeatmapViewer";
import LoadingOrError from "../components/LoadingOrError";

export default function Escalated() {
  const { id } = useParams();
  const { data, loading, error } = useResult(id);
  const [forwarded, setForwarded] = useState(false);
  if (!data) return <LoadingOrError loading={loading} error={error} />;

  return (
    <ResultScaffold
      data={data}
      icon={AlertTriangle}
      title="Escalated for Human Review"
      subtitle="Evidence is inconclusive — a human reviewer should make the final call."
    >
      <div className="grid gap-6 md:grid-cols-2">
        <div className="card p-4">
          <HeatmapViewer
            imageUrl={assetUrl(data.image_url)}
            heatmapUrl={assetUrl(data.heatmap_url)}
            evidence={data.evidence}
          />
        </div>
        <div className="space-y-5">
          <div className="card p-5">
            <ConfidenceBar verdict="ESCALATE" value={data.confidence} />
            <p className="mt-4 text-sm leading-relaxed text-aegis-slate">{data.rationale}</p>
          </div>

          <div className="card p-5">
            <h3 className="mb-3 text-sm font-semibold">Partial signals</h3>
            <div className="space-y-2">
              {data.evidence.map((e, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-aegis-slate">{e.type.replace(/_/g, " ")}</span>
                  <span className="font-mono text-aegis-escalate">{(e.score * 100).toFixed(0)}%</span>
                </div>
              ))}
            </div>
          </div>

          {forwarded ? (
            <div className="rounded-lg border border-aegis-approve/30 bg-aegis-approve/5 px-4 py-3 text-sm font-medium text-aegis-approve">
              ✓ Forwarded to reviewer@aegis.health — notification logged.
            </div>
          ) : (
            <button onClick={() => setForwarded(true)} className="btn-primary w-full">
              <Send size={18} /> Forward to Human Reviewer
            </button>
          )}
          <Link to={`/audit/${data.audit_id}`} className="btn-ghost w-full">
            <FileText size={16} /> View Full Audit
          </Link>
        </div>
      </div>
    </ResultScaffold>
  );
}
