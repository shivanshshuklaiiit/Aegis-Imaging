import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowLeft, ChevronDown, Link2 } from "lucide-react";
import clsx from "clsx";
import { useResult } from "../useResult";
import { assetUrl } from "../api";
import VerdictBadge from "../components/VerdictBadge";
import HeatmapViewer from "../components/HeatmapViewer";
import LoadingOrError from "../components/LoadingOrError";

function shortHash(h: string) {
  if (!h) return "—";
  return h.length > 14 ? `${h.slice(0, 8)}…${h.slice(-4)}` : h;
}

function AgentJson({ name, json, index }: { name: string; json: any; index: number }) {
  const [open, setOpen] = useState(false);
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.05 * index }}
      className="overflow-hidden rounded-xl border border-aegis-border"
    >
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between bg-aegis-bg px-4 py-3 text-left transition-colors hover:bg-aegis-border/40"
      >
        <span className="text-sm font-semibold capitalize text-aegis-navy">{name} agent</span>
        <motion.span animate={{ rotate: open ? 0 : -90 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={16} />
        </motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
          >
            <pre className="overflow-x-auto bg-aegis-ink px-4 py-3 text-xs leading-relaxed text-emerald-200">
              {JSON.stringify(json, null, 2)}
            </pre>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

export default function AuditDetail() {
  const { id } = useParams();
  const { data, loading, error } = useResult(id);
  if (!data) return <LoadingOrError loading={loading} error={error} />;

  const agents = Object.entries(data.agent_outputs || {});

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/dashboard" className="btn-ghost">
          <ArrowLeft size={16} /> Dashboard
        </Link>
        <VerdictBadge verdict={data.verdict} />
      </div>

      <div>
        <h1 className="font-mono text-2xl font-bold text-aegis-navy">{data.audit_id}</h1>
        <p className="text-sm text-aegis-slate">
          {data.modality?.toUpperCase()} · {data.total_latency_ms} ms · ${data.total_cost_usd.toFixed(4)}
          {data.created_at && ` · ${new Date(data.created_at).toLocaleString()}`}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="card p-4">
          <HeatmapViewer
            imageUrl={assetUrl(data.image_url)}
            heatmapUrl={assetUrl(data.heatmap_url)}
            evidence={data.evidence}
            showOverlayDefault={data.verdict !== "APPROVE"}
          />
        </div>
        <div className="card p-5">
          <h3 className="mb-2 text-sm font-semibold">Verdict & rationale</h3>
          <p className="text-sm leading-relaxed text-aegis-slate">{data.rationale || "—"}</p>
          <div className="mt-4 text-sm">
            <span className="text-aegis-slate">Confidence: </span>
            <span className="font-mono font-semibold text-aegis-navy">
              {(data.confidence * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Agent JSON */}
      <div>
        <h3 className="mb-3 text-sm font-semibold">Agent outputs</h3>
        <div className="space-y-2">
          {agents.length > 0 ? (
            agents.map(([name, json], i) => <AgentJson key={name} name={name} json={json} index={i} />)
          ) : (
            <p className="text-sm text-aegis-slate">No agent output recorded for this archived row.</p>
          )}
        </div>
      </div>

      {/* Hash chain visual */}
      <div>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold">
          <Link2 size={16} /> Tamper-evident hash chain
        </h3>
        <div className="flex flex-col items-stretch gap-3 md:flex-row md:items-center">
          {[
            { label: "Previous record", hash: data.hash_chain.prev, tone: "muted" },
            { label: "This record", hash: data.hash_chain.self, tone: "active" },
            { label: "Next record", hash: "", tone: "pending" },
          ].map((box, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.15 * i, type: "spring", stiffness: 260, damping: 22 }}
              className="flex flex-1 items-center gap-3"
            >
              <div
                className={clsx(
                  "flex-1 rounded-xl border p-4",
                  box.tone === "active"
                    ? "border-aegis-navy bg-navy-sheen text-white shadow-lift"
                    : "border-aegis-border bg-white"
                )}
              >
                <div className={clsx("text-xs font-medium", box.tone === "active" ? "text-white/70" : "text-aegis-slate")}>
                  {box.label}
                </div>
                <div className={clsx("mt-1 font-mono text-sm", box.tone === "active" ? "text-white" : "text-aegis-navy")}>
                  {box.hash ? shortHash(box.hash) : "pending…"}
                </div>
              </div>
              {i < 2 && <span className="hidden text-aegis-slate md:block">→</span>}
            </motion.div>
          ))}
        </div>
        <p className="mt-2 text-xs text-aegis-slate">
          SHA-256 of each record links to the previous one. Altering any field breaks every
          downstream hash — making the audit log tamper-evident.
        </p>
      </div>
    </div>
  );
}
