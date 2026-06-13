# 03 — Component Architecture

Ownership: **Zaki owns all components; Stitch owns only their skin** (08_*). Every component below is structure + data-binding; visual values come from tokens.

## Shared components (used on 2+ pages)

| Component | Renders | Data source |
|---|---|---|
| AppShell | sidebar + top bar + outlet | — |
| ImpactTicker | 3 mini counters, persistent top bar | impact events + `/impact/summary` |
| GradeBadge | S/A/B/C/Recycle chip (D→"Recycle" label rule lives HERE, once) | `grade` field |
| ConfidenceChip | high/medium/"Under review" (low) | `confidence` field |
| StatCounter | animated count-up number (mono font slot) | any numeric |
| EventCard | base card for feed entries, stage chips ASSESSED→ASSIGNED | WS events |
| RULRange | "4.3 yrs (3.1–5.2)" with band visualization | `rul_years`, `rul_range` |
| EmptyState | "Awaiting fleet ingestion —" pattern | — |

## Page components (single-page owners)

- **P1:** IndiaMap (+BatteryMarker, SiteMarker, DeploymentArc) · LiveDecisionFeed (+FeedFilter All/Assessments/Deployments) · FleetPulse · JobProgress · SafetySavesCard · SystemStatus · NationalCounter (hero)
- **P4:** Dropzone · RunDemoButton · SchemaCheckTable · PreviewTable · RejectReport · LaunchButton
- **P2/P5:** AadhaarPassport (+QRBlock, IDDecoder animation) · LifeStory · LifecycleTimeline · HealthPanel (+SoHGauge) · ExplainabilityPanel (+ShapBar) · DeploymentCard (+CounterfactualRow) — P5 reuses all in a single-column public layout, no shell
- **P3:** HeroCounters · GradeDonut · SiteTypeBreakdown · MiningAvoidedPanel · CircularityDial · MethodologyFootnote · India2030Overlay
- **P6:** FleetTable (+FilterChips, StatusBadge) · **P7:** SiteCard grid (+DemandGauge) + mini-map

## Data components (the only I/O owners)

| Component | Owns |
|---|---|
| QueryProvider | TanStack Query client; all REST via typed hooks (`useBatteries`, `useBatteryDetail`, `useAadhaar`, `useSites`, `useImpact`, `useJob`) |
| LiveFeedProvider | WS connection OR polling loop (env flag); event queue, rAF drain, ring-buffer reconciliation; exposes `useLiveFeed(filter?)` |
| lib/api.ts | fetch wrapper: base URL, error-envelope parsing, demo-key header |
| lib/types.ts | hand-mirrored types from docs/04 + ml-plan/01 — THE seam contract in TS form |

Rule: feature components receive data via props/hooks; zero fetch/socket calls outside the data layer.

## Visualization components — implementation notes

- **IndiaMap:** react-leaflet, CartoDB dark tiles, fixed India bounds, zoom locked during cascade (no judge-distracting drift). Markers = divIcons with grade token colors; DeploymentArc = animated polyline (CSS dash offset — cheap, smooth) from battery latlng → site latlng (both in the deployment event payload).
- **ShapBar:** horizontal signed bars from `explanation_json` (`label` + `shap` magnitude + `impact` sign) — no chart library needed, divs suffice.
- **GradeDonut/FleetPulse:** Recharts; data accumulates from assessment events during cascade, reconciles with `/impact/summary.by_grade` on `job_done`.
- **CircularityDial / SoHGauge:** Recharts radial or plain SVG arc — whichever is faster to skin; decide at implementation, both acceptable.
- **IDDecoder:** the 21-char string with segment-by-segment label reveal (country·mfr·chem·V·kWh·date·serial from `decoded`) — a 10-second wow that is literally seven spans and a stagger animation slot.

## Build-priority tags (mirrors blueprint tiers)

Critical: everything on P1/P2/P3/P4/P5 main path. Important: FleetTable, CounterfactualRow, MiningAvoidedPanel, CircularityDial. Optional: P7 components, IDDecoder animation polish (static decode acceptable), India2030 animation (hard cut to scaled numbers acceptable).
