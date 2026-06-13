# 11 — Deployment Recommendation Engine (optimization, NOT ML)

Transparent multi-criteria scoring per the architecture rule and docs/06 — every recommendation must carry reasons; a learned ranker can't testify. **Code placement:** pure scoring lives in `ml/recommend.py`; backend `services/deployment.py` wraps it (live site state in, persistence + capacity decrement out). This keeps the engine unit-testable and Antigravity-generatable in isolation.

## Inputs

From `assess()`: soh_pct, rul_cycles/years, grade, confidence. From battery_meta: rated_capacity_kwh, lat/lng. From backend: sites list (docs/03 schema) with `remaining_kwh` live. Constants: scoring weights, carbon factor, distance normalizer (shared/constants.py).

## Stage 1 — hard gates (eliminate, don't penalize)

```
grade D            → recyclers only, exactly 1 recommendation, stop
confidence low     → no recommendations, status "inspection" (08_*)
site.min_grade     → battery tier must meet it (S>A>B>C ordering)
site.min_soh_pct   → soh floor
site.remaining_kwh ≤ 0 → site full
tier suitability   → 10_grading_strategy map
```

## Stage 2 — score every surviving (battery, site) pair

```
raw = 0.30·capacity_match + 0.25·grade_headroom + 0.20·proximity + 0.15·carbon_benefit + 0.10·site_priority
```

(weights identical to docs/06 — one source of truth)

- `capacity_match` = 1 − |usable_kwh − site_unit_need| / site_unit_need, clipped [0,1]
- `grade_headroom` = 1.0 exact tier fit; −0.15 per tier of overshoot (an S in street lighting wastes national value — the penalty IS a story)
- `proximity` = 1 − haversine_km / 2000, clipped [0,1]
- `carbon_benefit` = normalized carbon_saved (docs/06 formula; 0 for D)
- `site_priority` = seeded weight (microgrids 1.3 — "policy is a parameter")

## Stage 3 — rank, select, explain

Sort descending → keep top 3 → `score_display = round(raw × 100)` (the 0–100 int of the output contract; raw float persisted in `deployments.score`). `selected_destination` = rank 1. Ties (<0.01): higher site_priority wins, then nearer.

Output per the contract (01_*): ranks 2–3 are not decoration — they are **exactly the data behind the "Why not?" counterfactual panel** (innovation #4): the UI renders rank-2 with its factor deltas ("Khavda BESS: −6 pts — 312 km farther"). One engine output powers selection, explanation, and counterfactual; nothing is computed twice.

Worked example (the contract's JSON): A-grade 4 kWh pack in Pune → Bhadla solar 87, Hyderabad ORR buffer 81, Gaya microgrid 74 → selected Bhadla; factors: "Best capacity match (3.3 of 4.0 kWh unit need)", "Grade A meets solar-storage bar", "High carbon offset vs new cells".

## Factor → English templates (same pattern as 09_*)

Top-3 factor contributions → strings: capacity_match → "Best capacity match ({usable:.1f} of {need:.1f} kWh unit need)" · proximity → "{km:.0f} km — nearest eligible {type}" · site_priority → "Rural microgrid priority applied" · grade_headroom → "Grade {g} meets {type} bar" · carbon_benefit → "High carbon offset vs new cells". Recycler routing: "Safety rule: grade Recycle routes to certified recycler" + "Est. recovery: {li:.1f} kg Li, {co:.1f} kg Co, {ni:.1f} kg Ni" (Material Recovery Receipt, innovation #6).

## Transport cost

Folded into `proximity` (distance is the demo-honest proxy for ₹/km logistics). A separate ₹ cost model is named-but-not-built (judge_attacks "what would you add"), and the transport-emissions answer (judge_attacks #71: 2–3 kg vs ~200 kg saved) stays valid because distance is already penalized.
