# 04 — Information Architecture

## Hierarchy (what outranks what, on every screen)

1. **Impact** — always visible (ImpactTicker, top bar, all pages). The mission is the frame.
2. **Decisions** — the primary content. Feeds, cards, arcs: every decision leads with its *reasons* (the 3 strings), then its destination. Reasons-first ordering is what separates "autonomous intelligence" from "dashboard."
3. **Identity** — depth on demand: click any battery → its passport. Identity is the reward for curiosity, not the landing content.
4. **Inventory** — tables/registries (P6/P7) exist for Q&A spelunking, lowest priority.

Corollary: numbers carry the hierarchy — every number gets the mono font slot, a label, and (where projected) the "(projected)" qualifier. A number without a label is a defect.

## The 20-second test (Mission Control must pass it cold)

A judge walking past the screen with zero context must extract, in order: **(1)** a national map of India with live activity (~3 s) → **(2)** "847 batteries processed today" hero counter (~5 s) → **(3)** a stream of cards each saying *grade + reason + destination* (~12 s) → conclusion: "this system is deciding what happens to India's batteries." Layout enforces the order: map dominates visually, counter dominates typographically, feed dominates motion. If any section needs explaining on stage, it has failed IA and gets simplified — copy is a crutch (the one allowed caption: the sub-hero line "Autonomous battery lifecycle decisions — live").

## User navigation (operator mental model)

Sidebar = noun-based (Mission Control / Fleet / Sites / Impact); one verb CTA (+ Ingest Fleet). Operator loop: ingest → watch → inspect → report. Maximum depth = 2 clicks from home to any fact (P1 → P2 → everything about one battery).

## Judge navigation (driven demo + free exploration)

Driven path = the 8-step demo flow (10_*). Free-exploration support (judges grab the mouse at tables): every visible element is clickable to its detail (markers, feed cards, donut segments → filtered fleet view if P6 built); nothing dead-ends; back always returns to Mission Control. The Q&A tabs (docs/09: grade-D passport, low-confidence battery, deployments view) are bookmarked states, reachable by URL.

## Content priorities under pressure (what gets cut from a screen first)

Per screen, last-in-first-out: P1 — SystemStatus chip → SafetySaves card detail (keep count) → FleetPulse; P2 — counterfactual row → IDDecoder animation; P3 — circularity dial → mining panel (keep the three hero counters to the end). The hero counters, map, feed, passport QR, and India 2030 number are never cut — they ARE the product story.

## Language rules (copy IA)

"Decided," never "processed," wherever a decision happened · "Recycle" never "D" in user-facing text · RUL always with its range · "simulated registry" label on site data (honesty in the pixels, judge_attacks #68) · Indian-English spellings consistent (centre/center: pick "Center" for product nouns, done) · no exclamation marks anywhere — command centers don't shout.
