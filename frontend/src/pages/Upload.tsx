import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { FileImage, Gauge, Lock, ShieldCheck, Sparkles, UploadCloud, X } from "lucide-react";
import clsx from "clsx";
import { setPending } from "../handoff";
import { Item, PageMotion, fadeUp } from "../motion";

const MODALITIES = [
  { id: "xray", label: "X-ray" },
  { id: "mri", label: "MRI" },
  { id: "ct", label: "CT" },
  { id: "ultrasound", label: "Ultrasound" },
  { id: "other", label: "Other" },
];

const MAX_BYTES = 20 * 1024 * 1024;
const ACCEPTED = ["image/png", "image/jpeg", "application/dicom"];

const TRUST = [
  { icon: Gauge, label: "< 2s verdict", sub: "P50 latency" },
  { icon: Sparkles, label: "5 AI agents", sub: "parallel panel" },
  { icon: Lock, label: "SHA-256 audit", sub: "tamper-evident" },
];

export default function Upload() {
  const nav = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [modality, setModality] = useState("xray");
  const [error, setError] = useState<string | null>(null);

  const accept = useCallback((f: File) => {
    setError(null);
    const isDicom = f.name.toLowerCase().endsWith(".dcm");
    if (!ACCEPTED.includes(f.type) && !isDicom) {
      setError("Unsupported format. Upload PNG, JPEG, or DICOM (.dcm).");
      return;
    }
    if (f.size > MAX_BYTES) {
      setError("File exceeds the 20 MB limit.");
      return;
    }
    setFile(f);
    setPreview(isDicom ? null : URL.createObjectURL(f));
  }, []);

  const onDrop = useCallback(
    (accepted: File[], rejected: any[]) => {
      if (rejected.length) {
        setError("File rejected. Check the format and size (max 20 MB).");
        return;
      }
      if (accepted[0]) accept(accepted[0]);
    },
    [accept]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    maxSize: MAX_BYTES,
  });

  function startVerify() {
    if (!file) return;
    setPending({ file, modality, previewUrl: preview || "" });
    nav(`/verifying/pending`);
  }

  return (
    <PageMotion className="mx-auto max-w-2xl">
      <div className="mb-10 text-center">
        <Item>
          <span className="eyebrow mb-4">
            <ShieldCheck size={14} className="text-aegis-signal" /> Agentic trust layer for medical imaging
          </span>
        </Item>
        <Item>
          <h1 className="text-balance text-4xl font-bold leading-[1.1] tracking-tightest md:text-5xl">
            Verify any scan
            <br />
            <span className="bg-gradient-to-r from-aegis-navy via-aegis-blue to-aegis-signal bg-clip-text text-transparent">
              before you trust it.
            </span>
          </h1>
        </Item>
        <Item>
          <p className="mx-auto mt-4 max-w-md text-pretty text-[15px] leading-relaxed text-aegis-muted">
            Five specialized AI agents inspect every image for tampering and synthetic
            generation — with a cryptographically auditable trail.
          </p>
        </Item>
      </div>

      <Item>
        <div className="card card-hover p-6 md:p-8">
          <AnimatePresence mode="wait">
            {!file ? (
              <motion.div
                key="drop"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                {...(getRootProps() as any)}
                className={clsx(
                  "group relative flex cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xl border-2 border-dashed px-6 py-16 text-center transition-all duration-300",
                  isDragActive
                    ? "border-aegis-signal bg-aegis-signal/5 shadow-glow"
                    : "border-aegis-border hover:border-aegis-blue/60 hover:bg-aegis-bg"
                )}
              >
                <input {...getInputProps()} />
                {/* animated scan sweep on hover/drag */}
                <div
                  className={clsx(
                    "pointer-events-none absolute inset-x-0 h-24 bg-gradient-to-b from-aegis-signal/15 to-transparent transition-opacity",
                    isDragActive ? "animate-scan-y opacity-100" : "opacity-0"
                  )}
                />
                <motion.div
                  animate={{ y: isDragActive ? -4 : 0 }}
                  className="mb-3 flex h-16 w-16 items-center justify-center rounded-2xl bg-aegis-navy/5 text-aegis-blue group-hover:bg-aegis-signal/10 group-hover:text-aegis-signal"
                >
                  <UploadCloud size={30} />
                </motion.div>
                <p className="font-semibold text-aegis-navy">
                  {isDragActive ? "Release to verify" : "Drag & drop an image, or click to browse"}
                </p>
                <p className="mt-1 text-sm text-aegis-muted">PNG, JPEG or DICOM · up to 20 MB</p>
              </motion.div>
            ) : (
              <motion.div
                key="file"
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.97 }}
                transition={{ type: "spring", stiffness: 300, damping: 24 }}
                className="flex items-center gap-4 rounded-xl border border-aegis-border bg-aegis-bg p-4"
              >
                <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-aegis-border bg-white">
                  {preview ? (
                    <img src={preview} alt="preview" className="h-full w-full object-cover" />
                  ) : (
                    <FileImage size={28} className="text-aegis-blue" />
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="truncate font-medium text-aegis-navy">{file.name}</div>
                  <div className="text-sm text-aegis-muted">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                    {!preview && " · DICOM (preview after conversion)"}
                  </div>
                </div>
                <motion.button
                  whileTap={{ scale: 0.9 }}
                  onClick={() => {
                    setFile(null);
                    setPreview(null);
                  }}
                  className="rounded-lg p-2 text-aegis-muted transition hover:bg-white hover:text-aegis-reject"
                  aria-label="Remove file"
                >
                  <X size={18} />
                </motion.button>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mt-4 overflow-hidden"
              >
                <div className="rounded-lg border border-aegis-reject/30 bg-aegis-reject/5 px-4 py-2.5 text-sm font-medium text-aegis-reject">
                  {error}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="mt-6">
            <label className="mb-2 block text-sm font-semibold text-aegis-navy">Modality</label>
            <div className="flex flex-wrap gap-2">
              {MODALITIES.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setModality(m.id)}
                  className={clsx(
                    "relative rounded-lg px-4 py-2 text-sm font-medium transition-colors",
                    modality === m.id ? "text-white" : "text-aegis-slate hover:text-aegis-navy"
                  )}
                >
                  {modality === m.id && (
                    <motion.span
                      layoutId="modality-pill"
                      className="absolute inset-0 -z-10 rounded-lg bg-aegis-navy"
                      transition={{ type: "spring", stiffness: 500, damping: 32 }}
                    />
                  )}
                  {modality !== m.id && (
                    <span className="absolute inset-0 -z-10 rounded-lg border border-aegis-border" />
                  )}
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <motion.button
            whileHover={{ scale: file ? 1.01 : 1 }}
            whileTap={{ scale: file ? 0.98 : 1 }}
            onClick={startVerify}
            disabled={!file}
            className="btn-primary mt-8 w-full overflow-hidden"
          >
            <ShieldCheck size={18} /> Verify Image
          </motion.button>
        </div>
      </Item>

      <motion.div variants={fadeUp} className="mt-6 grid grid-cols-3 gap-3">
        {TRUST.map((t) => (
          <div key={t.label} className="card flex flex-col items-center gap-1 px-3 py-4 text-center">
            <t.icon size={18} className="text-aegis-signal" />
            <div className="text-sm font-semibold text-aegis-navy">{t.label}</div>
            <div className="text-[11px] text-aegis-muted">{t.sub}</div>
          </div>
        ))}
      </motion.div>

      <Item>
        <p className="mt-6 text-center text-xs text-aegis-muted">
          Press <kbd className="rounded border border-aegis-border bg-white px-1.5 py-0.5 font-mono">U</kbd> for
          upload · <kbd className="rounded border border-aegis-border bg-white px-1.5 py-0.5 font-mono">D</kbd> for
          dashboard
        </p>
      </Item>
    </PageMotion>
  );
}
