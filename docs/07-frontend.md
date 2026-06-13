# 07 — Frontend (Owner: Zaki)

Target feel: **Tesla Fleet Control × Palantir ops room.** Dark, dense, alive. The dashboard *is* the demo — judges remember what they saw, not what you said.

## Stack

Vite + React 18 + **TypeScript** (loose tsconfig — types mirror the frozen contracts, see frontend-plan/07) · Tailwind CSS · **TanStack Query** (all REST state) · Recharts · react-leaflet (CartoDB `dark_matter` tiles — free, **no API key**) · `qrcode.react` · `framer-motion` (counters only — don't animate everything). State: TanStack cache + one LiveFeed context; no Redux/Zustand.

## Design tokens (commit as `tailwind.config` extensions, hour 1)

> **Status: placeholder values.** Final visual design arrives from Stitch as token values only (deadline H18, else these ship — handoff contract in frontend-plan/08). Structure never changes at skin time.

```
bg base      #0A0E1A      panel        #111827 (1px border #1F2937)
accent       #10B981 (volt green)      accent-2  #FACC15 (warning amber)
text         #E5E7EB / #9CA3AF muted
grades       S #A855F7 · A #10B981 · B #3B82F6 · C #F59E0B · D #EF4444  (use EVERYWHERE — badges, map pins, charts; D labeled "Recycle" in UI)
fonts        Inter (UI) · JetBrains Mono (every number, ID, and counter)
```

Rules: numbers always mono. One glow effect max (the impact counters). No light mode. No stock photos. Empty states say "Awaiting fleet ingestion —" not "No data."

## Component tree

```
App
├─ AppShell (sidebar nav + top bar)
│  └─ ImpactTicker (top bar: ⚡ MWh · 🌱 tCO₂e · ♻ diverted — animated count-up)
├─ pages/
│  ├─ CommandCenter            ← THE DEMO PAGE, 80% of effort
│  │  ├─ IndiaMap (react-leaflet)
│  │  │  ├─ BatteryMarker (pulse on assess, grade color)
│  │  │  ├─ SiteMarker (icon by type, fill = % demand met)
│  │  │  └─ DeploymentArc (animated battery→site polyline)
│  │  ├─ LiveDecisionFeed (right rail: scrolling event cards, newest top)
│  │  │  └─ DecisionCard (grade badge · SoH · RUL±band · site · 3 reasons)
│  │  ├─ FleetPulse (grade distribution bar, fills live)
│  │  └─ JobProgress (847-battery progress bar + ETA)
│  ├─ FleetTable (sort/filter by grade/status → row click → detail)
│  ├─ BatteryDetail
│  │  ├─ AadhaarPassport (QR · 21-char ID with decoded segments · static/dynamic panels)
│  │  ├─ LifecycleTimeline (vertical, from lifecycle_events)
│  │  ├─ HealthPanel (SoH gauge · RUL with interval band · confidence chip)
│  │  ├─ ExplainabilityPanel (3 reasons + SHAP-style horizontal impact bars)
│  │  └─ DeploymentCard (site, score factors, distance, impact)
│  ├─ SitesView (registry cards + mini-map)            ← CUT FIRST if behind
│  ├─ UploadWizard (drag CSV → column check → preview 5 rows → LAUNCH button)
│  ├─ ImpactCenter (/impact: hero counters · grade donut · India2030Overlay)
│  └─ PublicPassport (/b/:aadhaarId — read-only, mobile-first, reuses P2 components, no nav chrome; QR target)
└─ lib/ (api client · useLiveFeed hook (WS + polling fallback) · formatters)
```

**Adopted innovation features (see innovation_features.md):** `LifeStory` paragraph on BatteryDetail + PublicPassport (renders `life_story` from the aadhaar endpoint) · `SafetySavesCard` on CommandCenter (derived from impact `by_grade` D-count + flag reasons) · `India2030Overlay` on ImpactCenter (frontend-only: scales `/impact/summary` to 128 GWh national volume — no new endpoint). Page inventory, tiers, and flows: see product_experience_blueprint.md (source of truth for UX).

## The wow moments (build in this order)

1. **Live cascade** — upload fires; markers pop with grade colors; feed scrolls; counters climb; arcs shoot across India. Backend paces ~0.15s/battery ≈ 2 min of theatre (doc 02).
2. **Aadhaar passport page** — QR + monospace 21-char ID with decoded segments labeled (country · mfr · chemistry · date · serial), timeline from manufacture → solar farm. The "BPAN-style static/dynamic split" callout lives here.
3. **Explainability bars** — judges have seen a hundred dashboards; they have not seen "why this grade" with signed impact bars on every battery.
4. **The big-screen close** — `/impact` route: three huge counters, grade donut, site-type breakdown. Final pitch slide = this page, live.

## useLiveFeed (the only tricky code — write it first)

```js
// VITE_USE_POLLING=false → WebSocket; true → poll GET /jobs/{id} every 1s
// Identical event objects out of both paths (recent_events is WS-shaped — doc 04).
// Buffer events into a queue; drain at ~6/s with requestAnimationFrame so the
// UI stays smooth even if the server bursts. Cap feed list at 100 DOM nodes.
```

Demo machine runs on `localhost` (doc 02) — flip to polling instantly if venue Wi-Fi mangles WS.

## Day-1 mock workflow

Hours 1–12 Zaki runs entirely on Farhan's mock server (doc 04): static JSON + looping WS replay of 30 events. Swap base URL at H12. Zero hours blocked on backend.

## Anti-scope

No auth screens, no settings page, no responsive mobile pass (demo is a laptop + projector — test at 1920×1080 AND the projector's real resolution), no dark/light toggle, no i18n. SitesView is the designated sacrifice (doc 10 cut-lines).
