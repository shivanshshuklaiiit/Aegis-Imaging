import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Activity,
  CheckCircle2,
  Database,
  XCircle,
} from "lucide-react";
import {
  Bar,
  BarChart,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { motion } from "framer-motion";
import { getDashboard, type DashboardResponse, type Verdict } from "../api";
import MetricTile from "../components/MetricTile";
import VerdictBadge from "../components/VerdictBadge";
import LoadingOrError from "../components/LoadingOrError";
import { CountUp, Reveal } from "../motion";

const VERDICT_COLOR: Record<Verdict, string> = {
  APPROVE: "#16A34A",
  REJECT: "#DC2626",
  ESCALATE: "#D97706",
};

export default function Dashboard() {
  const nav = useNavigate();
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"ALL" | Verdict>("ALL");

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, []);

  const pieData = useMemo(() => {
    if (!data) return [];
    return [
      { name: "Approve", value: data.totals.approve, key: "APPROVE" as Verdict },
      { name: "Reject", value: data.totals.reject, key: "REJECT" as Verdict },
      { name: "Escalate", value: data.totals.escalate, key: "ESCALATE" as Verdict },
    ];
  }, [data]);

  const costData = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.cost.by_model).map(([model, usd]) => ({
      model: model.replace(/-instruct|-vision/g, ""),
      usd: +usd.toFixed(4),
    }));
  }, [data]);

  const latencyData = useMemo(() => {
    if (!data) return [];
    return [...data.recent_audits]
      .reverse()
      .map((a, i) => ({ i: i + 1, ms: a.total_latency_ms }));
  }, [data]);

  if (!data) return <LoadingOrError loading={loading} error={error} />;

  const rows = data.recent_audits.filter((r) => filter === "ALL" || r.verdict === filter);

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold">Operations Dashboard</h1>
          <p className="text-sm text-aegis-slate">Live verification metrics & IronLabs routing</p>
        </div>
      </div>

      {/* Metric tiles */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricTile label="Verifications Today" value={data.totals.verifications_today} icon={Activity} accent="signal" />
        <MetricTile label="Approved" value={data.totals.approve} icon={CheckCircle2} accent="approve" />
        <MetricTile label="Rejected" value={data.totals.reject} icon={XCircle} accent="reject" />
        <MetricTile
          label="Avg Latency (P50)"
          value={data.latency.p50_ms / 1000}
          decimals={2}
          suffix="s"
          sub={`P95 ${(data.latency.p95_ms / 1000).toFixed(2)}s`}
          icon={Database}
        />
      </div>

      {/* IronLabs savings banner */}
      <Reveal>
        <div className="card relative flex flex-wrap items-center justify-between gap-4 overflow-hidden bg-navy-sheen p-6 text-white">
          <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-aegis-signal/20 blur-3xl" />
          <div className="relative">
            <div className="text-sm font-medium text-white/70">IronLabs smart routing savings</div>
            <div className="text-5xl font-bold tracking-tight text-aegis-signal">
              <CountUp value={data.cost.saved_percent} decimals={1} suffix="%" />
            </div>
            <div className="text-sm text-white/70">cost saved vs. all-top-tier models</div>
          </div>
          <div className="relative text-right">
            <div className="text-sm text-white/70">Total spend today</div>
            <div className="font-mono text-2xl font-semibold">
              <CountUp value={data.cost.total_usd} decimals={3} prefix="$" />
            </div>
            <div className="text-xs text-white/60">saved ${data.cost.saved_vs_top_tier_usd.toFixed(2)}</div>
          </div>
        </div>
      </Reveal>

      {/* Charts */}
      <Reveal className="grid gap-4 lg:grid-cols-3">
        <div className="card p-5">
          <h3 className="mb-4 text-sm font-semibold">Verdict breakdown</h3>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={pieData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={3}>
                {pieData.map((d) => (
                  <Cell key={d.key} fill={VERDICT_COLOR[d.key]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-2 flex justify-center gap-4 text-xs">
            {pieData.map((d) => (
              <span key={d.key} className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: VERDICT_COLOR[d.key] }} />
                {d.name} ({d.value})
              </span>
            ))}
          </div>
        </div>

        <div className="card p-5">
          <h3 className="mb-4 text-sm font-semibold">Cost by model tier (USD)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={costData} margin={{ left: -10 }}>
              <XAxis dataKey="model" tick={{ fontSize: 10 }} interval={0} angle={-15} textAnchor="end" height={50} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="usd" fill="#2E5C8A" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h3 className="mb-4 text-sm font-semibold">Latency trend (ms)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={latencyData} margin={{ left: -10 }}>
              <XAxis dataKey="i" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Line type="monotone" dataKey="ms" stroke="#0F2A47" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Reveal>

      {/* Audit table */}
      <Reveal className="card overflow-hidden">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-aegis-border px-5 py-4">
          <h3 className="text-sm font-semibold">Recent audit log</h3>
          <div className="flex gap-1">
            {(["ALL", "APPROVE", "REJECT", "ESCALATE"] as const).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={
                  "rounded-md px-3 py-1 text-xs font-medium transition " +
                  (filter === f ? "bg-aegis-navy text-white" : "text-aegis-slate hover:bg-aegis-bg")
                }
              >
                {f === "ALL" ? "All" : f.charAt(0) + f.slice(1).toLowerCase()}
              </button>
            ))}
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-aegis-border text-left text-xs uppercase tracking-wide text-aegis-slate">
                <th className="px-5 py-3 font-medium">Audit ID</th>
                <th className="px-5 py-3 font-medium">Verdict</th>
                <th className="px-5 py-3 font-medium">Modality</th>
                <th className="px-5 py-3 font-medium">Confidence</th>
                <th className="px-5 py-3 font-medium">Latency</th>
                <th className="px-5 py-3 font-medium">Cost</th>
                <th className="px-5 py-3 font-medium">Time</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <motion.tr
                  key={r.audit_id}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: Math.min(i * 0.04, 0.4) }}
                  onClick={() => nav(`/audit/${r.audit_id}`)}
                  className="group cursor-pointer border-b border-aegis-border last:border-0 transition-colors hover:bg-aegis-signal/[0.04]"
                >
                  <td className="px-5 py-3 font-mono text-xs text-aegis-navy group-hover:text-aegis-signal">{r.audit_id}</td>
                  <td className="px-5 py-3"><VerdictBadge verdict={r.verdict} size="sm" /></td>
                  <td className="px-5 py-3 uppercase text-aegis-slate">{r.modality || "—"}</td>
                  <td className="px-5 py-3 font-mono tnum">{(r.confidence * 100).toFixed(0)}%</td>
                  <td className="px-5 py-3 font-mono tnum">{r.total_latency_ms} ms</td>
                  <td className="px-5 py-3 font-mono tnum">${r.total_cost_usd.toFixed(4)}</td>
                  <td className="px-5 py-3 text-xs text-aegis-slate">
                    {new Date(r.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </td>
                </motion.tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-aegis-slate">
                    No records for this filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Reveal>
    </div>
  );
}
