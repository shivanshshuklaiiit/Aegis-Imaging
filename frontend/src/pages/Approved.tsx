import { Link, useParams } from "react-router-dom";
import { ArrowRight, CheckCircle2, FileText } from "lucide-react";
import { useResult } from "../useResult";
import { assetUrl } from "../api";
import ResultScaffold, { ConfidenceBar } from "../components/ResultScaffold";
import LoadingOrError from "../components/LoadingOrError";

export default function Approved() {
  const { id } = useParams();
  const { data, loading, error } = useResult(id);
  if (!data) return <LoadingOrError loading={loading} error={error} />;

  return (
    <ResultScaffold
      data={data}
      icon={CheckCircle2}
      title="Image Approved"
      subtitle="This scan is authentic and safe to use in clinical workflows."
    >
      <div className="grid gap-6 md:grid-cols-2">
        <div className="card overflow-hidden">
          <img
            src={assetUrl(data.image_url) || assetUrl(data.heatmap_url) || ""}
            alt="Approved scan"
            className="max-h-[420px] w-full object-contain bg-aegis-navy/5"
          />
        </div>
        <div className="space-y-5">
          <div className="card p-5">
            <ConfidenceBar verdict="APPROVE" value={data.confidence} />
            <p className="mt-4 text-sm leading-relaxed text-aegis-slate">{data.rationale}</p>
          </div>
          <div className="card p-5">
            <h3 className="mb-2 text-sm font-semibold">Why it passed</h3>
            <ul className="space-y-2 text-sm text-aegis-slate">
              <li className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-aegis-approve" /> No generative artifacts detected
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-aegis-approve" /> Metadata complete & consistent
              </li>
              <li className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-aegis-approve" /> Anatomy clinically plausible
              </li>
            </ul>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to={`/processing/${data.audit_id}`} className="btn-primary flex-1">
              Continue to Processing <ArrowRight size={18} />
            </Link>
            <Link to={`/audit/${data.audit_id}`} className="btn-ghost">
              <FileText size={16} /> Audit
            </Link>
          </div>
        </div>
      </div>
    </ResultScaffold>
  );
}
