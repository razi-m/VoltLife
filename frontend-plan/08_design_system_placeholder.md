# 08 — Design System Placeholder (Stitch handoff contract)

| | |
|---|---|
| **Current design status** | Placeholder |
| **Final design source** | Stitch |
| **Owner** | Zaki |
| **Status** | Pending |

## How this works

The frontend builds **structure now, skin later**. The placeholder tokens are the current values in docs/07 (dark bg `#0A0E1A`, volt green accent, 5 grade colors incl. S `#A855F7`, Inter/JetBrains Mono, etc.) — they ship as Tailwind config + CSS custom properties, and they are good enough to win with if Stitch never lands. Stitch's deliverable replaces token *values*, not component structure.

## Required design tokens (the slots Stitch must fill — names frozen)

- **Color:** `surface-base`, `surface-panel`, `surface-border`, `accent-primary`, `accent-warning`, `text-primary`, `text-muted`, `grade-s/a/b/c/d` (5 — non-negotiable count), `status-ok/warn/error`, `map-marker-pulse`
- **Type:** `font-ui`, `font-mono` (every number/ID — IA rule), scale `display/h1/h2/body/caption/micro`
- **Space & shape:** 4-px-base spacing scale, `radius-card/chip/button`, `border-hairline`
- **Motion:** `duration-fast/medium/counter` (count-up = 400 ms placeholder), `easing-standard`; **reduced-motion variant required** (projectors + recording)
- **Elevation:** max ONE glow effect token (`glow-impact`) — reserved for impact counters (docs/07 rule)

## Required layout rules (architecture-owned — Stitch may style, not move)

Persistent top-bar ImpactTicker on all shell pages · map visually dominant on Mission Control · feed as right rail, newest-on-top · P5 public passport single-column mobile-first · dark theme only · no layout shift during cascade (reserved space for counters/feed — numbers changing must never reflow the page).

## Required component categories to skin

Cards (EventCard family) · badges/chips (GradeBadge, ConfidenceChip, stage chips) · counters (StatCounter, hero counters) · panels (passport, health, explainability) · map elements (markers, arcs, tooltips) · charts (donut, pulse bar, SHAP bars, gauges) · inputs (dropzone, buttons, filter chips) · empty states.

## Handoff rules + deadline (this is a cut-line, treat it like one)

1. Stitch output lands as **token values + per-category styling only** — any change requiring component restructuring is rejected (it's H20+; structure is frozen).
2. **Deadline H18.** After H18 the placeholder ships, and it ships proudly — the placeholder follows docs/07's full design language and passed the original blueprint review.
3. Skinning is a ≤2-hour job by construction: if applying Stitch's design takes longer, the deliverable violated rule 1 — revert to placeholder, no debate (docs/10 cut-line discipline).
4. No new colors/fonts smuggled in via component styles — tokens or nothing; a `grep` for hex codes outside the token file is part of the done-check.
