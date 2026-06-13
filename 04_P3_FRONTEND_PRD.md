# P3 — Frontend Lead PRD

**Role:** UX & Demo Polish
**Owner:** P3
**Reports to:** P1 for API contract, P4 for branding/copy

---

## 1. Mission

Own every pixel the judges see. Build all 7 screens with production-quality polish, an enterprise-grade visual identity (Aegis = shield = trust), and the animated agent pipeline that creates the demo's "aha" moment. The product *is* the UI for 80% of the pitch — make it look like a real Series A healthtech company shipped it.

---

## 2. Deliverables

| # | Deliverable | Definition of Done |
|---|---|---|
| D1 | Vite + React + TS + Tailwind scaffold | Builds clean, hot reload works, deployed to localhost:5173 |
| D2 | Aegis brand kit | Logo SVG (shield), color tokens, typography in `tailwind.config.js` |
| D3 | Upload page | Drag-drop, modality selector, file validation, "Verify" button |
| D4 | Verifying page | 5 animated agent cards lighting up sequentially, latency counter |
| D5 | Approved page | Green banner, image + verdict, "Continue to Processing →" CTA |
| D6 | Rejected page | Red banner, image with heatmap overlay, evidence list, audit link |
| D7 | Escalated page | Amber banner, "Forward to Human Reviewer" CTA |
| D8 | Dashboard page | Live metrics, recharts (verdict pie, cost bars, latency line), audit table |
| D9 | Audit Detail page | Single record with full agent JSON (collapsible), hash chain visual |
| D10 | API client (`api.ts`) | Typed fetch wrappers, error handling, mock mode for offline dev |
| D11 | Demo backup video | 90-second screen recording of full happy path (insurance) |

---

## 3. Hour-by-Hour Plan

### Sprint 1: Foundation (H0–H2)

- `npm create vite@latest aegis-frontend -- --template react-ts`
- Install: `tailwindcss`, `recharts`, `lucide-react`, `react-router-dom`, `clsx`
- Configure Tailwind with Aegis design tokens (see §4 below)
- Set up router with all 7 routes (with placeholder pages)
- **At H2 sync: lock API contract with P1**

### Sprint 2: Upload + Verifying (H2–H6)

- Build Upload page:
  - Centered card layout, generous whitespace
  - Drag-drop zone with `react-dropzone`
  - Modality selector (segmented control: X-ray / MRI / CT / Other)
  - File validation: max 20MB, PNG/JPEG/DICOM
  - Big primary "Verify Image" CTA
- Build Verifying page:
  - 5 agent cards in a row
  - Each card has: icon, name, status (pending → running → done)
  - Sequential reveal animation using `setTimeout` chained to backend response stream (or simulated if backend is stub)
  - Live timer "Elapsed: 1.42s"
  - On verdict received → route to result page based on verdict

### Sprint 3: Result Pages (H6–H12)

- Approved page: green color block, large checkmark icon, image preview, verdict card (confidence as progress bar), CTA "Continue to Processing →" which routes to a mock `/processing` page
- Rejected page: red color block, image with heatmap overlay (use `<img>` with `heatmap_url`), evidence list as cards, audit ID prominent, "View Full Audit" link
- Escalated page: amber color block, partial evidence, "Forward to Human Reviewer" CTA + email mock

### Sprint 4: Dashboard + Audit (H12–H18)

- Dashboard page:
  - Top row: 4 metric tiles (Today, Approved, Rejected, Avg Latency)
  - Middle row: verdict pie chart + cost-by-model bar chart (recharts)
  - Bottom: live audit log table with filtering, click row → audit detail
  - "IronLabs Savings" big number: "68.6% cost saved vs all-top-tier"
- Audit Detail page:
  - Image + heatmap side by side
  - Verdict + rationale
  - 5 collapsible cards (one per agent) showing full JSON output
  - Hash chain visualization: 3 boxes (prev hash → this hash → next hash) with SHA values

### Sprint 5: Real Integration (H18–H24)

- Wire all pages to real backend
- Handle loading states, error states, empty states
- Test with real images from P2's set
- Fix layout bugs at common viewport sizes (1280×800, 1920×1080 — judges' projector likely 1080p)

### Sprint 6: Polish (H24–H30)

- Animation pass: fade-ins, smooth route transitions (Framer Motion if time permits, else CSS)
- Empty states with helpful illustrations
- Error toasts (use `sonner` or custom)
- Keyboard shortcuts: `U` for upload, `D` for dashboard
- Verify dark mode looks fine if a judge toggles it

### Sprint 7: Demo Mode (H30–H34)

- Add `?demo=hero1` query param that auto-loads a cached verdict for the demo
- Record backup video using OBS or Loom (90 seconds, full happy path + rejection)
- Project on a second monitor at H32 to test how it looks on a big screen

### Sprint 8: Standby (H34–H36)

- Be at the demo machine
- Have the backup video on a USB drive

---

## 4. Aegis Brand Kit

### Colors (Tailwind tokens)

```js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      aegis: {
        navy:   "#0F2A47",  // primary brand
        blue:   "#2E5C8A",  // secondary
        slate:  "#475569",  // text
        bg:     "#F8FAFC",  // page background
        card:   "#FFFFFF",  // surface
        approve:"#16A34A",  // green
        reject: "#DC2626",  // red
        escalate:"#D97706", // amber
        border: "#E2E8F0",
      },
    },
    fontFamily: {
      sans: ["Inter", "system-ui", "sans-serif"],
      mono: ["JetBrains Mono", "monospace"],
    },
  },
}
```

### Logo Concept

Simple SVG shield with "A" inside, in navy `#0F2A47`. One-color, scalable. Don't waste 2 hours on this — keep it minimal.

```html
<svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <path d="M16 2 L28 7 V16 C28 23 22 28 16 30 C10 28 4 23 4 16 V7 Z"
        fill="#0F2A47"/>
  <text x="16" y="22" text-anchor="middle" font-family="Inter"
        font-weight="700" font-size="14" fill="white">A</text>
</svg>
```

### Typography

- Headings: Inter 600, generous line-height (1.3)
- Body: Inter 400, 16px base
- Mono: JetBrains Mono for hashes, JSON, audit IDs

### Layout Rhythm

- Max content width 1280px
- Page padding: 32px desktop, 16px mobile
- Card padding: 24px
- Generous whitespace — enterprise apps look "expensive" because of breathing room

### Iconography

Use `lucide-react`. Suggested icons:
- Shield (brand), Upload, Loader, Check, X, AlertTriangle, FileSearch, Activity, Database

---

## 5. The "Aha" Moment: Verifying Page Animation

This is the single most important UI moment. Spend extra time here.

```tsx
const AGENTS = [
  { name: "Intake & Metadata", icon: FileSearch },
  { name: "Visual Forensics",  icon: Eye },
  { name: "Clinical Plausibility", icon: Stethoscope },
  { name: "Verdict Officer",   icon: Gavel },
  { name: "Audit & Compliance", icon: Shield },
];

// On mount, simulate sequential reveal even if backend responds in one shot.
// Stagger by 250ms each so user perceives multi-agent reasoning.
useEffect(() => {
  AGENTS.forEach((_, i) => {
    setTimeout(() => setStep(i + 1), 250 * (i + 1));
  });
}, []);
```

Each card animates: gray → pulsing blue → green checkmark.

Underneath: live counter `1.42s` ticking up. Subtitle: *"5 specialized agents are inspecting your image..."*

---

## 6. Screen Inventory

| Route | Screen | Trigger | Notes |
|---|---|---|---|
| `/` | Upload | Default | Hero of the app |
| `/verifying/:id` | Verifying | After upload | Animated cards |
| `/result/approved/:id` | Approved | Verdict APPROVE | Green |
| `/result/rejected/:id` | Rejected | Verdict REJECT | Red + heatmap |
| `/result/escalated/:id` | Escalated | Verdict ESCALATE | Amber |
| `/processing/:id` | Mock Processing | Click "Continue" on Approved | Just a placeholder showing routing worked |
| `/dashboard` | Dashboard | Nav | Live metrics |
| `/audit/:id` | Audit Detail | Click row in dashboard | Full record |

---

## 7. API Client Skeleton (`src/api.ts`)

```ts
const BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

export type Verdict = "APPROVE" | "REJECT" | "ESCALATE";

export interface VerifyResponse {
  audit_id: string;
  verdict: Verdict;
  confidence: number;
  rationale: string;
  evidence: Array<{ type: string; region?: number[]; score: number; source_agent: string }>;
  heatmap_url: string | null;
  agent_outputs: Record<string, any>;
  total_latency_ms: number;
  total_cost_usd: number;
  hash_chain: { prev: string; self: string };
}

export async function verifyImage(file: File, modality: string): Promise<VerifyResponse> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("modality", modality);
  const r = await fetch(`${BASE}/api/v1/verify`, { method: "POST", body: fd });
  if (!r.ok) throw new Error(`Verify failed: ${r.status}`);
  return r.json();
}

export async function getDashboard() { /* ... */ }
export async function getAudit(id: string) { /* ... */ }
```

---

## 8. Success Criteria

By H30 you must have:
- ✅ All 7 routes render without console errors
- ✅ Real upload → real verdict → correct result page
- ✅ Heatmap displays correctly on rejected page
- ✅ Dashboard shows live numbers from backend
- ✅ Looks crisp at 1920×1080 (judge projector)
- ✅ Verifying animation works even if backend returns instantly
- ✅ Backup video recorded

---

## 9. Things That Will Bite You

1. **Tailwind purge will eat dynamic class names.** Don't do `bg-${color}-500`; use a map.
2. **Images from backend won't load if CORS isn't right.** Have P1 set `Access-Control-Allow-Origin: *` on `/static`.
3. **DICOM files don't render in `<img>`.** Show the image only after backend converts to PNG.
4. **recharts is heavy.** Lazy-load the Dashboard page.
5. **Drag-drop on Safari is finicky.** Test on Chrome (which judges will use).
6. **Don't ship console.logs.** They look unprofessional during a screen-share.

---

## 10. Daily Checkpoints

- **H2:** Scaffold up, contracts locked
- **H6:** Upload + Verifying pages working with stub backend
- **H12:** All result pages built
- **H18:** Dashboard + Audit Detail done
- **H24:** Fully integrated with real backend
- **H30:** Polish pass complete
- **H34:** Backup video recorded
