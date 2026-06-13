import { Link, useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, CheckCircle2, Workflow } from "lucide-react";

const STEPS = [
  "Verdict written to audit log with hash chain",
  "Mock EHR webhook delivered (/mock-ehr)",
  "Mock claims webhook delivered (/mock-claims)",
];

export default function Processing() {
  const { id } = useParams();
  return (
    <div className="mx-auto max-w-xl py-10 text-center">
      <motion.div
        initial={{ scale: 0, rotate: -20 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: "spring", stiffness: 220, damping: 14 }}
        className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-aegis-approve/10"
      >
        <Workflow size={32} className="text-aegis-approve" />
      </motion.div>
      <motion.h1
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="text-2xl font-bold"
      >
        Routed to downstream processing
      </motion.h1>
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.18 }}
        className="mt-2 text-aegis-muted"
      >
        The verified scan <span className="font-mono text-aegis-navy">{id}</span> has been handed
        off to your clinical / claims workflow. Aegis has attached the audit trail to the record.
      </motion.p>

      <div className="card mt-8 space-y-3 p-6 text-left">
        {STEPS.map((s, i) => (
          <motion.div
            key={s}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 + i * 0.15 }}
            className="flex items-center gap-2.5 text-sm text-aegis-slate"
          >
            <CheckCircle2 size={16} className="shrink-0 text-aegis-approve" /> {s}
          </motion.div>
        ))}
      </div>

      <div className="mt-8 flex justify-center gap-3">
        <Link to="/" className="btn-ghost">
          <ArrowLeft size={16} /> Verify another
        </Link>
        <Link to={`/audit/${id}`} className="btn-primary">
          View Audit Record
        </Link>
      </div>
    </div>
  );
}
