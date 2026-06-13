import type { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";
import clsx from "clsx";
import { CountUp } from "../motion";

export default function MetricTile({
  label,
  value,
  display,
  sub,
  icon: Icon,
  accent = "navy",
  decimals = 0,
  prefix = "",
  suffix = "",
}: {
  label: string;
  /** numeric value to count up to */
  value: number;
  /** optional fully-formatted override (skips count-up) */
  display?: string;
  sub?: string;
  icon?: LucideIcon;
  accent?: "navy" | "approve" | "reject" | "escalate" | "signal";
  decimals?: number;
  prefix?: string;
  suffix?: string;
}) {
  const accents: Record<string, string> = {
    navy: "text-aegis-navy bg-aegis-navy/10",
    approve: "text-aegis-approve bg-aegis-approve/10",
    reject: "text-aegis-reject bg-aegis-reject/10",
    escalate: "text-aegis-escalate bg-aegis-escalate/10",
    signal: "text-aegis-signal bg-aegis-signal/10",
  };
  return (
    <motion.div whileHover={{ y: -3 }} transition={{ type: "spring", stiffness: 400, damping: 24 }} className="card card-hover p-5">
      <div className="flex items-start justify-between">
        <span className="text-sm font-medium text-aegis-muted">{label}</span>
        {Icon && (
          <span className={clsx("rounded-lg p-1.5", accents[accent])}>
            <Icon size={18} />
          </span>
        )}
      </div>
      <div className="mt-2 text-3xl font-bold tracking-tight text-aegis-ink">
        {display ?? <CountUp value={value} decimals={decimals} prefix={prefix} suffix={suffix} />}
      </div>
      {sub && <div className="mt-1 text-xs text-aegis-muted">{sub}</div>}
    </motion.div>
  );
}
