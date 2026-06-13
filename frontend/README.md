# Aegis Imaging — Frontend

React 18 + Vite + TypeScript + Tailwind. Implements all 7 screens from `04_P3_FRONTEND_PRD.md`.

## Run

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # type-check + production bundle
```

## Backend & mock mode

The API client (`src/api.ts`) talks to the FastAPI backend at `VITE_API_BASE`
(default `http://localhost:8000`). If the backend is unreachable it **auto-falls
back to a built-in mock** (`src/mock.ts`) so the demo always works offline.

Control via `.env` (copy from `.env.example`):

- `VITE_MOCK=true` — always use mock data (shows a "Demo Mode" badge)
- `VITE_MOCK=false` — never mock; surface backend errors
- unset — try backend, fall back to mock on failure

Mock verdicts are keyword-driven by filename for repeatable demos: include
`fake`/`ai`/`synthetic` → REJECT, `ambiguous`/`old`/`film` → ESCALATE,
`real`/`genuine` → APPROVE.

## Routes

| Route | Screen |
|---|---|
| `/` | Upload |
| `/verifying/:id` | Animated 5-agent pipeline |
| `/result/approved/:id` | Approved (green) |
| `/result/rejected/:id` | Rejected (red + heatmap) |
| `/result/escalated/:id` | Escalated (amber) |
| `/processing/:id` | Mock downstream routing |
| `/dashboard` | Metrics, charts, audit log (lazy-loaded) |
| `/audit/:id` | Full record, agent JSON, hash chain |

Keyboard: `U` → Upload, `D` → Dashboard.
