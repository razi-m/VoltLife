# 01 — Frontend Architecture (BINDING for Antigravity)

One idea on every screen: **India's Battery Command Center** — an autonomous national platform, not a dashboard. Architecturally that means: decisions are the content, impact is always visible, and nothing on screen is invented by the frontend.

## Layers

```
Routes (React Router)
  └─ Pages (blueprint P1–P7 — composition only, no logic)
       └─ Feature components (DecisionCard, AadhaarPassport, IndiaMap, …)
            └─ Data layer:
                 • TanStack Query  → all REST state (queries keyed per endpoint)
                 • LiveFeedProvider → WS/polling stream (single context)
            └─ lib/: api client · types (mirroring frozen contracts) · constants · formatters
```

Stack: React 18 + Vite + **TypeScript** + **TanStack Query** (this round's additions, synced to docs/07) + Tailwind + Recharts + react-leaflet + qrcode.react. TS pragmatism rule: types exist to mirror the frozen contracts (`lib/types.ts` is hand-written from docs/04 + ml-plan/01); `tsconfig` stays loose (`strict: false` acceptable) — TS is here for seam safety, not type golf.

## The no-invention rule (display-only, with exactly four exceptions)

The frontend renders backend/ML data verbatim. The ONLY frontend-computed values, all pre-declared in integration_validation §4 + backend-plan/09:

1. **India 2030 finale** — `impact.summary × (128 GWh ÷ batch GWh)`
2. **Safety Saves reason chips** — client aggregation of streamed grade-D `reasons`
3. **Mining avoided** — `carbon_saved_tonnes × 1000/60 × {Li .10, Co .13, Ni .40}` kg/kWh
4. **Circularity score** — backend-plan/09 formula over summary fields

Constants for 1/3/4 come from a `lib/constants.ts` that mirrors `shared/constants.py` values — same numbers, documented as mirrored. Anything else computed client-side is a defect.

## Data-flow responsibilities

- REST (TanStack Query) = **state**: what exists now (fleet, detail, sites, impact, passport).
- Stream (LiveFeedProvider) = **motion**: what just happened (assessment/deployment/impact events).
- Reconciliation: stream events update UI optimistically during a cascade; `job_done` invalidates the relevant queries so REST truth wins at rest. No event is ever the long-term source of truth.

## Component boundaries

Pages compose; feature components own their slice of rendering; the two data providers own all I/O. No component fetches directly; no component opens its own socket. The visual skin (colors/type/spacing) is a swappable layer pending Stitch (08_design_system_placeholder.md) — components must be skinnable without structural change: semantic class hooks / token variables only, zero hard-coded styling values inside component logic.

## System-flow storytelling (mandated)

The pipeline (Upload → ML → Decision → Aadhaar → Impact) is communicated by the **demo journey itself** (pages in that order) plus one persistent cue: each DecisionCard carries stage chips (ASSESSED → ASSIGNED) so the flow is legible on every event, not in a diagram. No architecture-explainer page — judges watch the flow happen.
