# 11 — Frontend Folder Structure & Build Order

Vite + React + TS template. The prompt's example folders map: `services/` → `lib/`, `contexts/` → `providers/`, `store/` → (deliberately none — 07_*), `layouts/` → `components/shell/`.

```
frontend/
├─ src/
│  ├─ main.tsx · App.tsx               # router, QueryProvider, LiveFeedProvider
│  ├─ pages/
│  │  ├─ MissionControl.tsx            # P1 (incl. deployments feed view via ?feed=)
│  │  ├─ Intake.tsx                    # P4
│  │  ├─ BatteryDetail.tsx             # P2
│  │  ├─ PublicPassport.tsx            # P5 (no shell)
│  │  ├─ ImpactCenter.tsx              # P3 (+ India2030 overlay)
│  │  ├─ Fleet.tsx                     # P6 (Tier 2)
│  │  └─ Sites.tsx                     # P7 (Tier 3 — first cut)
│  ├─ components/
│  │  ├─ shell/                        # AppShell, Sidebar, TopBar, ImpactTicker, SystemStatus
│  │  ├─ shared/                       # GradeBadge, ConfidenceChip, StatCounter, EventCard,
│  │  │                                #   RULRange, EmptyState
│  │  ├─ map/                          # IndiaMap, BatteryMarker, SiteMarker, DeploymentArc
│  │  ├─ feed/                         # LiveDecisionFeed, FeedFilter, DecisionCard, JobProgress,
│  │  │                                #   FleetPulse, SafetySavesCard, NationalCounter
│  │  ├─ passport/                     # AadhaarPassport, QRBlock, IDDecoder, LifeStory,
│  │  │                                #   LifecycleTimeline, HealthPanel, ExplainabilityPanel,
│  │  │                                #   ShapBar, DeploymentCard, CounterfactualRow
│  │  ├─ impact/                       # HeroCounters, GradeDonut, SiteTypeBreakdown,
│  │  │                                #   MiningAvoidedPanel, CircularityDial, India2030Overlay,
│  │  │                                #   MethodologyFootnote
│  │  └─ intake/                       # Dropzone, RunDemoButton, SchemaCheckTable, PreviewTable,
│  │                                   #   RejectReport, LaunchButton
│  ├─ providers/                       # QueryProvider.tsx, LiveFeedProvider.tsx, AppContext.tsx
│  ├─ hooks/                           # useBatteries, useBatteryDetail, useAadhaar, useSites,
│  │                                   #   useImpact, useJob, useHealth, useLiveFeed
│  ├─ lib/
│  │  ├─ api.ts                        # fetch wrapper + error envelope (05_*)
│  │  ├─ types.ts                      # mirrored frozen contracts (07_*)
│  │  ├─ constants.ts                  # mirrors shared/constants.py values (derived-data math)
│  │  ├─ demo.ts                       # hero battery ids, hotkey chords, sample CSV import
│  │  └─ format.ts                     # numbers, units, "(projected)" labels
│  ├─ styles/tokens.css                # placeholder tokens — THE Stitch replacement surface (08_*)
│  └─ assets/sample_fleet.csv          # RunDemoButton payload
├─ index.html · vite.config.ts · tailwind.config.ts · tsconfig.json (loose) · .env.example
```

`.env`: `VITE_API_BASE`, `VITE_WS_URL`, `VITE_USE_POLLING`, `VITE_DEMO_KEY`.

## Build order (Antigravity sequence; acceptance per step)

| Step | Deliverable | Done when |
|---|---|---|
| 1 | lib/ (api, types, constants) + providers + shell + tokens.css | app boots against mock server; types compile against docs/04 example JSON pasted verbatim |
| 2 | LiveFeedProvider (BOTH paths) + feed/ components | mock WS loop renders cascading cards; flag flip to polling → identical |
| 3 | MissionControl assembly (map + feed + counters + progress) | full fake cascade on mocks looks like the demo |
| 4 | Intake page | sample CSV → preview → launch round-trips against the mock |
| 5 | BatteryDetail + passport/ components | mock passport renders complete incl. SHAP bars + Life Story |
| 6 | PublicPassport (mobile-first) + ImpactCenter + India2030 | phone-width render clean; finale overlay works with hard-cut numbers |
| 7 | Fleet table · reconciliation polish · EmptyStates sweep | every page has designed zero-data and error states |
| 8 | Demo dev-panel + hotkeys + real-backend swap | one env change moves from mocks to real backend with zero code edits |
| 9 | (post-H18 only) Stitch token application | ≤2 h, token values only, hex-grep passes (08_* rule 4) |

Steps 1–3 are the day-one block (docs/10 H1–6 for Zaki). Step 9 is optional by design.
