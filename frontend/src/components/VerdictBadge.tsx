import { AlertTriangle, Check, X } from "lucide-react";
import clsx from "clsx";
import type { Verdict } from "../api";

// Static class maps — never interpolate Tailwind class names (purge eats them).
const STYLES: Record<Verdict, { wrap: string; icon: typeof Check; label: string }> = {
  APPROVE: { wrap: "bg-aegis-approve/10 text-aegis-approve border-aegis-approve/30", icon: Check, label: "Approved" },
  REJECT: { wrap: "bg-aegis-reject/10 text-aegis-reject border-aegis-reject/30", icon: X, label: "Rejected" },
  ESCALATE: { wrap: "bg-aegis-escalate/10 text-aegis-escalate border-aegis-escalate/30", icon: AlertTriangle, label: "Escalated" },
};

export default function VerdictBadge({ verdict, size = "md" }: { verdict: Verdict; size?: "sm" | "md" }) {
  const s = STYLES[verdict];
  const Icon = s.icon;
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border font-semibold",
        s.wrap,
        size === "sm" ? "px-2.5 py-0.5 text-xs" : "px-3 py-1 text-sm"
      )}
    >
      <Icon size={size === "sm" ? 13 : 15} strokeWidth={2.5} />
      {s.label}
    </span>
  );
}
