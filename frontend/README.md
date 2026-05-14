# Regulatory Compliance – Frontend

React + Vite + TypeScript SPA for the AI Regulatory Compliance Platform.

## Run

```bash
cd frontend
npm install
npm run dev
```

Backend at `http://localhost:8000` is proxied via `/api`.

## Pages

- `/login` — Sign in / register (with organization)
- `/` — Dashboard with compliance stats and recent alerts
- `/regulations` — Browse, filter (jurisdiction, category), search
- `/regulations/:id` — Detail with requirements + start assessment
- `/assessments` — List with score bars and status badges
- `/assessments/:id` — Findings, recommendations, risk items, run AI assessment
- `/alerts` — Mark read, dismiss, generate alerts
- `/ai/analyze` — Analyze raw regulation text
- `/ai/risk` — Organization risk profile
- `/ai/gap` — Gap analysis vs. selected regulation
- `/ai/policy` — Generate downloadable policy document
