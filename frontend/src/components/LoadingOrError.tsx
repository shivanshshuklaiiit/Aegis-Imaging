import { Link } from "react-router-dom";
import { Loader2 } from "lucide-react";

export default function LoadingOrError({
  loading,
  error,
}: {
  loading: boolean;
  error: string | null;
}) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-aegis-slate">
        <Loader2 size={32} className="animate-spin text-aegis-blue" />
        <p className="mt-3 text-sm">Loading record…</p>
      </div>
    );
  }
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <p className="text-lg font-semibold text-aegis-navy">Record not found</p>
      <p className="mt-1 text-sm text-aegis-slate">{error || "This audit record is unavailable."}</p>
      <Link to="/dashboard" className="btn-ghost mt-4">
        Back to Dashboard
      </Link>
    </div>
  );
}
