import { Suspense, lazy } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import Navbar from "./components/Navbar";
import Upload from "./pages/Upload";
import Verifying from "./pages/Verifying";
import Approved from "./pages/Approved";
import Rejected from "./pages/Rejected";
import Escalated from "./pages/Escalated";
import Processing from "./pages/Processing";
import AuditDetail from "./pages/AuditDetail";
import { EASE } from "./motion";

// recharts is heavy — lazy-load the dashboard.
const Dashboard = lazy(() => import("./pages/Dashboard"));

function RouteTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.32, ease: EASE }}
    >
      {children}
    </motion.div>
  );
}

export default function App() {
  const location = useLocation();
  return (
    <div className="min-h-screen">
      <div className="app-backdrop" aria-hidden />
      <Navbar />
      <main className="mx-auto max-w-content px-4 py-10 md:px-8">
        <Suspense fallback={<div className="py-20 text-center text-aegis-slate">Loading…</div>}>
          <AnimatePresence mode="wait">
            <RouteTransition key={location.pathname}>
              <Routes location={location}>
                <Route path="/" element={<Upload />} />
                <Route path="/verifying/:id" element={<Verifying />} />
                <Route path="/result/approved/:id" element={<Approved />} />
                <Route path="/result/rejected/:id" element={<Rejected />} />
                <Route path="/result/escalated/:id" element={<Escalated />} />
                <Route path="/processing/:id" element={<Processing />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/audit/:id" element={<AuditDetail />} />
                <Route path="*" element={<Upload />} />
              </Routes>
            </RouteTransition>
          </AnimatePresence>
        </Suspense>
      </main>
    </div>
  );
}
