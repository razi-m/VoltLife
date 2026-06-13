# 14 — Demo Validation Harness (`tests/test_demo_validation.py`)

Purpose: no battery on stage may ever show an impossible number. Run offline (no backend, no DB — pure ML path) at fleet sizes **100, 500, 847**, generated fresh by the fleet generator each run. Runs: tonight after training · H20 · before every dry run · after ANY change to generator, model, or constants.

## Invariants (hard asserts — any failure blocks the demo)

| # | Invariant |
|---|---|
| 1 | `0 ≤ soh_pct ≤ 100` for every battery |
| 2 | `rul_cycles ≥ 0` and `rul_years ≥ 0` — no negative RUL, ever |
| 3 | `rul_low ≤ rul_years ≤ rul_high` (interval ordering) |
| 4 | `rul_years ≤ 8.0` (display clamp applied) |
| 5 | `grade ∈ {S, A, B, C, D}` and consistent with thresholds given the soh/flags (recompute and compare) |
| 6 | Every grade-D battery: exactly 1 recommendation, and it is a recycler; `energy_unlocked == carbon_saved == 0` |
| 7 | No S/A battery recommended to street_lighting (suitability gates hold) |
| 8 | `confidence ∈ {high, medium, low}`; **low ≤ 2% of fleet** (else fix the generator, per 08_*) |
| 9 | Low-confidence batteries have zero site recommendations (inspection routing) |
| 10 | `len(reasons) == 3`, all non-empty, no raw feature names (template coverage check) |
| 11 | 1–3 recommendations, integer scores 0–100, strictly descending; `selected_destination == recommendations[0]` |
| 12 | No NaN/Inf in any output field |
| 13 | Aggregate site assignments respect `remaining_kwh` (no site over-filled) |

## Distribution & plausibility checks (warn, review before demo)

- Grade mix within ±7 pts of target (S 5 / A 15 / B 35 / C 30 / D 15) at n=847
- SoH distribution roughly 55–92% band; fewer than 1% outside
- Counter sanity vs docs/06 worked example: total `energy_unlocked` ∈ [1.2, 3.0] GWh, `carbon_saved` ∈ [90, 180] t for 847 — the demo's closing numbers must land plausible (doc 12 R13)
- Hero-battery check: at least 5 grade-A batteries with clean stories exist (SoH 80–88, confidence high, solar destination) — pick the hero from this list (docs/09)

## Performance gate

847 batteries end-to-end (features→assess→recommend) **< 5 s unpaced** on the demo laptop — proves the 2-min cascade is theatrical pacing, not compute (judge_attacks #35 demo-ably true).

## Output

Prints a QA report (pass/fail per invariant, distribution table, runtime) and writes `tests/qa_report_latest.json`. The H30 backup video is recorded only after a green report.
