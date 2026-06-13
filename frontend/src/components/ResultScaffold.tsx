import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import clsx from "clsx";
import type { Verdict, VerifyResponse } from "../api";
import { EASE } from "../motion";

const BANNER: Record<Verdict, string> = {
  APPROVE: "from-aegis-approve to-emerald-600",
  REJECT: "from-aegis-reject to-rose-600",
  ESCALATE: "from-aegis-escalate to-amber-600",
};

const BAR: Record<Verdict, string> = {
  APPROVE: "bg-aegis-approve",
  REJECT: "bg-aegis-reject",
  ESCALATE: "bg-aegis-escalate",
};

export function ConfidenceBar({ verdict, value }: { verdict: Verdict; value: number }) {
  return (
    <div>
      <div className="mb-1.5 flex justify-between text-xs font-medium text-aegis-slate">
        <span>Confidence</span>
        <span className="font-mono tnum">{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="h-2.5 w-full overflow-hidden rounded-full bg-aegis-border">
        <motion.div
          className={clsx("h-full rounded-full", BAR[verdict])}
          initial={{ width: 0 }}
          animate={{ width: `${value * 100}%` }}
          transition={{ duration: 0.9, ease: EASE, delay: 0.2 }}
        />
      </div>
    </div>
  );
}

export default function ResultScaffold({
  data,
  icon: Icon,
  title,
  subtitle,
  children,
}: {
  data: VerifyResponse;
  icon: LucideIcon;
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: -16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: EASE }}
        className={clsx(
          "relative mb-6 flex items-center gap-4 overflow-hidden rounded-2xl bg-gradient-to-r px-6 py-5 text-white shadow-lift",
          BANNER[data.verdict]
        )}
      >
        {/* sheen */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-tr from-white/0 via-white/10 to-white/0" />
        <motion.div
          initial={{ scale: 0, rotate: -20 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 260, damping: 16, delay: 0.15 }}
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white/20 backdrop-blur"
        >
          <Icon size={28} strokeWidth={2.5} />
        </motion.div>
        <div>
          <div className="text-xl font-bold tracking-tight">{title}</div>
          <div className="text-sm text-white/90">{subtitle}</div>
        </div>
        <div className="ml-auto text-right">
          <div className="font-mono text-sm text-white/85 tnum">{data.audit_id}</div>
          <div className="text-xs text-white/70 tnum">
            {data.total_latency_ms} ms · ${data.total_cost_usd.toFixed(4)}
          </div>
        </div>
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: EASE, delay: 0.12 }}
      >
        {children}
      </motion.div>
    </div>
  );
}
