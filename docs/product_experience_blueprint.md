# Product Experience Blueprint (Owner: Zaid · Implementer: Zaki)

Source of truth for pages, navigation, flows, and the judged experience. Frontend (doc 07) implements this; doc 04 supplies every byte shown. Includes the three adopted innovation features (Life Story, India 2030 Finale, Safety Saves — see innovation_features.md).

## 1. Page count

**Total: 7** · **Required (Tier 1): 5** · **Optional (Tier 2): 1** · **Demo-only/cuttable (Tier 3): 1**

| # | Page | Route | Tier |
|---|---|---|---|
| P1 | Command Center | `/` | 1 |
| P2 | Battery Detail + Aadhaar Passport | `/battery/:id` | 1 |
| P3 | Impact Center (+ India 2030 Finale) | `/impact` | 1 |
| P4 | Upload Wizard | `/upload` (or modal from P1) | 1 |
| P5 | Public Passport (QR target, read-only) | `/b/:aadhaarId` | 1 |
| P6 | Fleet Table | `/fleet` | 2 |
| P7 | Sites Registry | `/sites` | 3 — first cut-line |

## 2. Navigation

```
AppShell
├─ Sidebar:  ⚡ Command Center · 🔋 Fleet · 🗺 Sites · 🌱 Impact
├─ Top bar:  ImpactTicker (always visible) · [+ Ingest Fleet] primary CTA → P4
└─ P5 is unlisted — reachable only via QR / direct link (it's a public artifact, not a nav item)

Flows: P4 →(launch)→ P1 →(click marker/feed card)→ P2 →(QR scan)→ P5 (judge's phone)
       P1 →(finale)→ P3 · P6 →(row click)→ P2 · P7 ↔ map tooltips if cut
```

## 3. Page specifications

### P1 — Command Center

- **Purpose:** The living proof that an autonomous system is running a national battery fleet. 80% of frontend effort.
- **Target user:** Judge (demo), fleet operator (story).
- **Displays:** India map (battery markers in grade colors, site markers, animated deployment arcs) · Live Decision Feed (assessment + deployment cards, 3 reasons each) · FleetPulse grade-distribution bar · Job progress (n/847 + ETA) · **Safety Saves card** (D-grade intercepts + flag reasons) · ImpactTicker (top bar).
- **Components:** IndiaMap, BatteryMarker, SiteMarker, DeploymentArc, LiveDecisionFeed (+ FeedFilter: All / Assessments / Deployments — the "Deployment Command Center" experience is this filter state, URL `?feed=deployments`, not a separate page), DecisionCard, FleetPulse, JobProgress, SafetySavesCard, ImpactTicker.
- **APIs:** `WS /ws/feed` (or `GET /jobs/{id}` polling) · `GET /sites` · `GET /impact/summary` (initial state).
- **Actions:** Pause/resume feed scroll · click marker/card → P2 · launch CTA → P4.
- **Demo importance:** **Critical** — the cascade lives here.
- **Wow:** map lighting up across India. **Story:** "every retired battery in the country, decided in seconds, safely."

### P2 — Battery Detail + Aadhaar Passport

- **Purpose:** One battery's complete identity — proof the system treats each unit individually.
- **Target user:** Judge, recycler, second-life buyer.
- **Displays:** AadhaarPassport (QR, 21-char ID with decoded segments, BPAN-style static/dynamic panels) · **Life Story paragraph** · LifecycleTimeline (manufacture → EV → assessment → destination) · HealthPanel (SoH gauge, RUL with interval band, confidence chip) · ExplainabilityPanel (3 reasons + signed impact bars) · DeploymentCard (site, score factors, distance, per-battery impact; counterfactual runner-up if built).
- **Components:** AadhaarPassport, LifeStory, LifecycleTimeline, HealthPanel, ExplainabilityPanel, DeploymentCard.
- **APIs:** `GET /batteries/{id}` · `GET /batteries/{id}/aadhaar`.
- **Actions:** Copy/scan QR · navigate timeline · back to P1/P6.
- **Demo importance:** **Critical** — the Aadhaar beat + emotional peak.
- **Wow:** decoded ID animating segment-by-segment; the Life Story. **Story:** "identity + biography = a battery you can trust second-hand."

### P3 — Impact Center

- **Purpose:** The scoreboard; converts decisions into planetary terms. Final pitch visual.
- **Target user:** Judge, policymaker.
- **Displays:** Three hero counters (MWh unlocked · tCO₂e avoided · batteries diverted) · grade donut · site-type breakdown · safety saves + responsibly recycled · methodology footnote (factors + citations, one click) · **India 2030 Finale overlay** (scale-to-128-GWh button → counters roll to national scale).
- **Components:** HeroCounters, GradeDonut, SiteTypeBreakdown, MethodologyFootnote, India2030Overlay.
- **APIs:** `GET /impact/summary`.
- **Actions:** Trigger 2030 overlay · toggle equivalence translation (if built).
- **Demo importance:** **Critical** — the close.
- **Wow:** the 2030 multiplication. **Story:** "847 was a demo. 128 GWh is the mandate. The system is the same."

### P4 — Upload Wizard

- **Purpose:** The inciting action — judges watch the fleet enter the system.
- **Target user:** Fleet operator (story), demo driver (reality).
- **Displays:** Dropzone · column-mapping check vs template · 5-row preview · reject report (count + reasons) · LAUNCH button.
- **Components:** Dropzone, SchemaCheckTable, PreviewTable, LaunchButton.
- **APIs:** `POST /batteries/ingest`.
- **Actions:** Drop CSV → preview → launch → auto-navigate to P1.
- **Demo importance:** **Critical but tiny** — ≤15 s on stage; build plain, not pretty.
- **Wow:** none needed (the wow is what happens next). **Story:** "one CSV is all an operator needs to start."

### P5 — Public Passport (QR target)

- **Purpose:** Judge-held artifact; BPAN's "anyone can verify" principle made real.
- **Target user:** Judge's phone; future: any buyer/recycler.
- **Displays:** Read-only condensed P2: ID + decoded segments, grade badge, SoH/RUL, Life Story, timeline, destination, per-battery impact. Mobile-first layout (the ONLY mobile-styled page).
- **Components:** Reuses P2 components in a single-column public layout; no nav chrome.
- **APIs:** `GET /aadhaar/{aadhaar_id}` (public, read-only).
- **Actions:** None — it's a certificate.
- **Demo importance:** **Critical** — the only moment a judge *touches* the product. Requires the Railway deploy live; printed hero-battery QR card as backup (doc 12 kit).
- **Wow:** product in the judge's pocket. **Story:** "trust travels with the battery, not with us."

### P6 — Fleet Table

- **Purpose:** Operator workhorse view; proves this is a tool, not a movie.
- **Target user:** Fleet operator, OEM.
- **Displays:** Sortable/filterable table (ID, OEM, chemistry, capacity, SoH, RUL, grade, confidence, status, destination) · grade filter chips · low-confidence filter (inspection queue lens, if built).
- **Components:** FleetTable, FilterChips, StatusBadge.
- **APIs:** `GET /batteries?grade&status&page`.
- **Actions:** Sort/filter/paginate · row click → P2.
- **Demo importance:** Important, not critical — 5 s drive-through on the way to P2, or skipped.

### P7 — Sites Registry (Tier 3 — first cut)

- **Purpose:** Demand-side visibility; where batteries *can* go.
- **Displays:** Site cards (type icon, location, min grade, demand gauge filling live) · mini-map.
- **APIs:** `GET /sites`.
- **Cut behavior:** site data survives as map tooltips on P1 — zero story lost.

## 4. Demo journey (exactly what judges experience)

```
P4 Upload (15 s: drop CSV → LAUNCH)
 → P1 Command Center (60–70 s: cascade — markers, feed, arcs, Safety Saves callout)
 → P2 Battery Detail (40 s: Aadhaar decode → Life Story → explainability bars)
 → P5 on judge's phone (10 s: scan QR — "keep it")
 → P3 Impact Center (20 s: counters land → India 2030 button → close line)
```

Total ≈ 2:45 of a 3-min demo. P6/P7 exist for Q&A spelunking, not the main path.

## 5. Wow + story per page (summary)

| Page | Wow | Sustainability story |
|---|---|---|
| P1 | India lights up, decisions stream | A country's waste stream, decided in real time — safely |
| P2 | ID decode + Life Story | Identity makes second life trustworthy |
| P3 | India 2030 multiplication | From batch to national mandate |
| P4 | (deliberately none) | Adoption is one CSV away |
| P5 | Product in judge's pocket | Trust travels with the battery |
| P6 | — | It's a daily tool, not a demo |
| P7 | Demand gauges filling | The grid is waiting for these batteries |

## 6. Prioritization

- **Tier 1 (must build):** P1, P2, P3, P4, P5
- **Tier 2 (if time allows):** P6 (it's mostly one table component — likely survives)
- **Tier 3 (demo-only/cut):** P7

## 7. Final recommendation

Minimum winning set = **Tier 1 (5 pages)**, where P4 is a modal-grade effort and P5 reuses P2's components — so the honest build surface is ~3.5 "real" pages. That set delivers the complete arc (ingest → autonomous decisions → identity → national impact), keeps AI visible on every screen (grades, reasons, RUL bands, decisions, extrapolation), and fits the doc 10 timeline with the three innovation features included. Anything beyond Tier 1 is earned, not planned.
