# 13 — Antigravity Implementation Guide (frontend)

**You are an implementer, not an architect, and not a designer.** Precedence on any apparent gap or conflict: **docs/04 api-contracts → integration_validation.md → ml-plan/01 → product_experience_blueprint.md → this folder → docs/07**. Report conflicts; never resolve them creatively.

## FROZEN — must not change

| Artifact | Status |
|---|---|
| 7 routes + page inventory (blueprint) — Deployment Command Center is a P1 view state, NOT a route | frozen |
| All API request/response shapes + WS event shapes (docs/04) → `lib/types.ts` mirrors them verbatim | frozen |
| Derived-data whitelist: India 2030, Safety Saves chips, mining avoided, circularity score — the ONLY frontend-computed values | frozen |
| Grade enum S/A/B/C/D + "Recycle" display mapping (GradeBadge, single location) | frozen |
| Dual live-feed paths (WS + polling), one provider, identical subscriber interface | frozen |
| Token slot names (08_*) and the structure-vs-skin boundary | frozen |
| Demo flow states (10_* checklist) — every listed state must exist | frozen |

## GENERATE — in the 11_* build order (acceptance criteria there)

lib + providers + shell → LiveFeedProvider + feed → MissionControl → Intake → BatteryDetail/passport → PublicPassport + ImpactCenter → Fleet + states sweep → dev-panel + backend swap. Sites page (P7) only if explicitly green-lit — it is the designated cut.

## RULES — non-negotiable

- **Never invent data.** No placeholder numbers, no `Math.random()`, no hardcoded impact values. Empty = EmptyState. The four whitelisted derivations cite their formula source in a comment.
- **No I/O outside the data layer** — components receive props/hooks only.
- **Events never write the Query cache** (07_* reconciliation protocol — accumulators + invalidate-on-done).
- **Styling via tokens only**: zero hex codes / font names / px literals in component files (hex-grep is part of done). Placeholder values live in `styles/tokens.css` + Tailwind config exclusively.
- **No additional dependencies** beyond: react, react-router, @tanstack/react-query, tailwind, recharts, react-leaflet + leaflet, qrcode.react. framer-motion optional for counters only. Anything else = ask.
- **TS pragmatism**: loose tsconfig; types exist for the seams, not for ceremony.
- **Performance floor**: cascade at 60 fps, feed capped at 100 nodes, rAF drain — jank is a functional defect (06_* checklist).
- **Accessibility floor**: reduced-motion variant, readable-at-projector type scale slots, keyboard hotkeys for the demo panel.

## Done means

Boots on mocks with one command · full fake cascade indistinguishable in structure from the real demo · env-swap to real backend with zero code edits · all 10_* states exist · both feed paths verified · phone-width P5 clean · hex-grep clean · the 20-second test passes with a stranger (literally: show someone Mission Control mid-cascade for 20 seconds, ask what the product does).

## Final audit (mandated 7 questions)

1. Integrates with backend? **YES** — 12 routes consumed per frozen contracts, mock-first, env-swap integration (05_*, 12_*).
2. Integrates with ML outputs? **YES** — every ML field rendered verbatim; enums, ranges, and explanation structures consumed as contracted; nothing recomputed (12_*).
3. Supports the demo? **YES** — all 8 steps mapped to actions/responses with per-step fallbacks (10_*); demo states are an explicit build checklist.
4. Supports WebSockets? **YES** — dedicated provider, 4 event types, reconnect ladder, polling twin (06_*).
5. Judges understand within 20 seconds? **YES** — the 20-second test is a designed, falsifiable acceptance criterion of Mission Control's IA (04_*), not a hope.
6. Buildable in 36 hours? **YES** — 8 build steps over ~3.5 effective pages, mock-first parallelism, Stitch as optional polish with a deadline, P7 pre-designated as the cut.
7. Increases winning probability? **YES** — the frontend is where the judges' entire experience happens: reasons-first cards, the Life Story, the phone-held passport, and the India 2030 close are the four moments this plan exists to guarantee.
