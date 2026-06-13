import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Check, Eye, FileSearch, Gavel, Loader2, Shield, Stethoscope, ScanLine } from "lucide-react";
import { verifyImage, type Verdict } from "../api";
import { cacheResult, takePending, clearPending } from "../handoff";
import { EASE } from "../motion";

const AGENTS = [
  { name: "Intake & Metadata", subtitle: "Hashing · EXIF / DICOM tags", icon: FileSearch },
  { name: "Visual Forensics", subtitle: "Generative artifact analysis", icon: Eye },
  { name: "Clinical Plausibility", subtitle: "Anatomy & modality check", icon: Stethoscope },
  { name: "Verdict Officer", subtitle: "Multi-source synthesis", icon: Gavel },
  { name: "Audit & Compliance", subtitle: "Hash chain · sign · log", icon: Shield },
];

const ROUTE: Record<Verdict, string> = {
  APPROVE: "/result/approved",
  REJECT: "/result/rejected",
  ESCALATE: "/result/escalated",
};

type Status = "pending" | "running" | "done";

export default function Verifying() {
  const nav = useNavigate();
  const [step, setStep] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [preview, setPreview] = useState<string | null>(null);
  const started = useRef(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;

    const pending = takePending();
    if (!pending) {
      nav("/", { replace: true });
      return;
    }
    setPreview(pending.previewUrl || null);

    const t0 = performance.now();
    const timer = setInterval(() => setElapsed((performance.now() - t0) / 1000), 40);

    const timeouts = AGENTS.map((_, i) =>
      setTimeout(() => setStep((s) => Math.max(s, i + 1)), 360 * (i + 1))
    );

    const minAnim = new Promise((r) => setTimeout(r, AGENTS.length * 360 + 300));
    Promise.all([verifyImage(pending.file, pending.modality), minAnim])
      .then(([res]) => {
        setStep(AGENTS.length);
        if (pending.previewUrl && !res.image_url) res.image_url = pending.previewUrl;
        cacheResult(res);
        clearPending();
        setTimeout(() => nav(`${ROUTE[res.verdict]}/${res.audit_id}`, { replace: true }), 450);
      })
      .catch(() => {
        clearPending();
        nav("/", { replace: true });
      });

    return () => {
      clearInterval(timer);
      timeouts.forEach(clearTimeout);
    };
  }, [nav]);

  const statusFor = (i: number): Status => (step > i ? "done" : step === i ? "running" : "pending");
  const progress = (step / AGENTS.length) * 100;

  return (
    <div className="mx-auto max-w-5xl py-4">
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 text-center"
      >
        <span className="eyebrow mb-3">
          <ScanLine size={14} className="text-aegis-signal" /> Live verification
        </span>
        <h1 className="text-2xl font-bold md:text-3xl">Inspecting your image…</h1>
        <p className="mt-1.5 text-aegis-muted">5 specialized agents are reasoning in parallel</p>
      </motion.div>

      <div className="grid items-stretch gap-6 lg:grid-cols-[420px_1fr]">
        {/* ── Scanner ─────────────────────────────────────────────── */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: EASE }}
          className="card relative overflow-hidden bg-navy-sheen p-4"
        >
          <div className="relative aspect-square w-full overflow-hidden rounded-xl bg-aegis-ink">
            {preview ? (
              <img src={preview} alt="scan" className="h-full w-full object-cover opacity-90" />
            ) : (
              <div
                className="h-full w-full opacity-40"
                style={{
                  backgroundImage:
                    "linear-gradient(rgba(34,211,238,0.25) 1px, transparent 1px), linear-gradient(90deg, rgba(34,211,238,0.25) 1px, transparent 1px)",
                  backgroundSize: "28px 28px",
                }}
              />
            )}

            {/* scanning beam */}
            <div className="pointer-events-none absolute inset-x-0 top-0 h-1/3 animate-scan-y bg-gradient-to-b from-aegis-signal/40 via-aegis-signal/10 to-transparent" />
            <div className="pointer-events-none absolute inset-x-0 animate-scan-y">
              <div className="h-0.5 w-full bg-aegis-signal shadow-[0_0_18px_4px_rgba(34,211,238,0.7)]" />
            </div>

            {/* targeting corner brackets */}
            {[
              "left-3 top-3 border-l-2 border-t-2",
              "right-3 top-3 border-r-2 border-t-2",
              "left-3 bottom-3 border-l-2 border-b-2",
              "right-3 bottom-3 border-r-2 border-b-2",
            ].map((c) => (
              <span key={c} className={`absolute h-6 w-6 rounded-[3px] border-aegis-signal/80 ${c}`} />
            ))}

            {/* crosshair */}
            <div className="pointer-events-none absolute left-1/2 top-1/2 h-10 w-10 -translate-x-1/2 -translate-y-1/2">
              <span className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-aegis-signal/50" />
              <span className="absolute top-1/2 left-0 h-px w-full -translate-y-1/2 bg-aegis-signal/50" />
            </div>
          </div>

          <div className="mt-4 flex items-end justify-between px-1">
            <div>
              <div className="font-mono text-4xl font-semibold text-white tnum">{elapsed.toFixed(2)}s</div>
              <div className="text-xs text-white/50">elapsed</div>
            </div>
            <div className="text-right">
              <div className="font-mono text-2xl font-semibold text-aegis-signal tnum">
                {Math.round(progress)}%
              </div>
              <div className="text-xs text-white/50">{step}/{AGENTS.length} agents</div>
            </div>
          </div>
        </motion.div>

        {/* ── Agent pipeline ──────────────────────────────────────── */}
        <div className="card relative p-5 md:p-6">
          {/* vertical connector track */}
          <div className="absolute bottom-9 left-[39px] top-11 w-0.5 rounded bg-aegis-border md:left-[43px]">
            <motion.div
              className="w-full rounded bg-gradient-to-b from-aegis-signal to-aegis-blue"
              initial={{ height: 0 }}
              animate={{ height: `${(Math.max(0, step - 0.5) / (AGENTS.length - 1)) * 100}%` }}
              transition={{ ease: EASE, duration: 0.4 }}
            />
          </div>

          <div className="space-y-1">
            {AGENTS.map((a, i) => {
              const status = statusFor(i);
              return (
                <motion.div
                  key={a.name}
                  initial={{ opacity: 0, x: 12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.1 + i * 0.08, ease: EASE }}
                  className="relative z-10 flex items-center gap-4 rounded-xl px-2 py-3"
                >
                  <div className="relative">
                    {status === "running" && (
                      <span className="absolute -inset-1 animate-ping rounded-full bg-aegis-signal/30" />
                    )}
                    <motion.div
                      animate={{
                        scale: status === "running" ? 1.05 : 1,
                      }}
                      className={
                        "relative flex h-9 w-9 items-center justify-center rounded-full border-2 transition-colors duration-300 " +
                        (status === "done"
                          ? "border-aegis-approve bg-aegis-approve text-white"
                          : status === "running"
                          ? "border-aegis-signal bg-white text-aegis-signal"
                          : "border-aegis-border bg-white text-aegis-muted")
                      }
                    >
                      <AnimatePresence mode="wait">
                        {status === "done" ? (
                          <motion.span key="d" initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 500, damping: 18 }}>
                            <Check size={18} strokeWidth={3} />
                          </motion.span>
                        ) : status === "running" ? (
                          <Loader2 key="r" size={18} className="animate-spin" />
                        ) : (
                          <a.icon key="p" size={17} />
                        )}
                      </AnimatePresence>
                    </motion.div>
                  </div>

                  <div className="flex-1">
                    <div className={"font-semibold transition-colors " + (status === "pending" ? "text-aegis-muted" : "text-aegis-navy")}>
                      {a.name}
                    </div>
                    <div className="text-xs text-aegis-muted">{a.subtitle}</div>
                  </div>

                  <span
                    className={
                      "rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide transition-colors " +
                      (status === "done"
                        ? "bg-aegis-approve/10 text-aegis-approve"
                        : status === "running"
                        ? "bg-aegis-signal/10 text-aegis-signal"
                        : "bg-aegis-bg text-aegis-muted")
                    }
                  >
                    {status}
                  </span>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
