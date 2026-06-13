import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { FileText, XCircle } from "lucide-react";
import { useResult } from "../useResult";
import { assetUrl } from "../api";
import ResultScaffold, { ConfidenceBar } from "../components/ResultScaffold";
import HeatmapViewer from "../components/HeatmapViewer";
import LoadingOrError from "../components/LoadingOrError";

export default function Rejected() {
  const { id } = useParams();
  const { data, loading, error } = useResult(id);
  if (!data) return <LoadingOrError loading={loading} error={error} />;

  return (
    <ResultScaffold
      data={data}
      icon={XCircle}
      title="Image Rejected"
      subtitle="This scan shows signs of synthetic generation or tampering."
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
            <ConfidenceBar verdict="REJECT" value={data.confidence} />
            <p className="mt-4 text-sm leading-relaxed text-aegis-slate">{data.rationale}</p>
          </div>

          <div className="card p-5">
            <h3 className="mb-3 text-sm font-semibold">Evidence</h3>
            <div className="space-y-2">
              {data.evidence.map((e, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.35 + i * 0.1 }}
                  className="flex items-center justify-between rounded-lg border border-aegis-border bg-aegis-bg px-3 py-2 transition-colors hover:border-aegis-reject/30"
                >
                  <div>
                    <div className="text-sm font-medium capitalize text-aegis-navy">
                      {e.type.replace(/_/g, " ")}
                    </div>
                    <div className="text-xs text-aegis-slate">
                      via {e.source_agent}
                      {e.region && ` · region [${e.region.join(", ")}]`}
                    </div>
                  </div>
                  <span className="font-mono text-sm font-semibold text-aegis-reject tnum">
                    {(e.score * 100).toFixed(0)}%
                  </span>
                </motion.div>
              ))}
              {data.evidence.length === 0 && (
                <p className="text-sm text-aegis-slate">No itemized evidence returned.</p>
              )}
            </div>
          </div>

          <Link to={`/audit/${data.audit_id}`} className="btn-primary w-full">
            <FileText size={18} /> View Full Audit
          </Link>
        </div>
      </div>
    </ResultScaffold>
  );
}
