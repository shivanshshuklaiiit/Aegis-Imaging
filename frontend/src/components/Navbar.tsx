import { Link, useLocation, useNavigate } from "react-router-dom";
import { LayoutDashboard, Upload } from "lucide-react";
import { useEffect } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";
import Logo from "./Logo";
import { FORCE_MOCK } from "../api";

const LINKS = [
  { to: "/", label: "Upload", icon: Upload, match: (p: string) => p === "/" },
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, match: (p: string) => p.startsWith("/dashboard") },
];

export default function Navbar() {
  const loc = useLocation();
  const nav = useNavigate();

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") return;
      if (e.key.toLowerCase() === "u") nav("/");
      if (e.key.toLowerCase() === "d") nav("/dashboard");
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [nav]);

  return (
    <header className="sticky top-0 z-30 border-b border-aegis-border/70 bg-white/70 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-content items-center justify-between px-4 md:px-8">
        <Link to="/" className="group flex items-center gap-2.5">
          <motion.div
            whileHover={{ rotate: -6, scale: 1.06 }}
            transition={{ type: "spring", stiffness: 400, damping: 15 }}
          >
            <Logo />
          </motion.div>
          <div className="leading-none">
            <div className="text-[15px] font-bold tracking-tight text-aegis-ink">Aegis Imaging</div>
            <div className="text-[11px] font-medium text-aegis-muted">Every scan, verified.</div>
          </div>
        </Link>

        <nav className="flex items-center gap-1">
          {LINKS.map(({ to, label, icon: Icon, match }) => {
            const active = match(loc.pathname);
            return (
              <Link
                key={to}
                to={to}
                className={clsx(
                  "relative inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors",
                  active ? "text-white" : "text-aegis-slate hover:text-aegis-navy"
                )}
              >
                {active && (
                  <motion.span
                    layoutId="nav-pill"
                    className="absolute inset-0 -z-10 rounded-lg bg-aegis-navy shadow-card"
                    transition={{ type: "spring", stiffness: 500, damping: 34 }}
                  />
                )}
                <Icon size={16} /> {label}
              </Link>
            );
          })}
          {FORCE_MOCK && (
            <span className="ml-2 inline-flex items-center gap-1.5 rounded-full bg-aegis-escalate/10 px-3 py-1 text-xs font-semibold text-aegis-escalate">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-aegis-escalate" /> Demo
            </span>
          )}
        </nav>
      </div>
    </header>
  );
}
