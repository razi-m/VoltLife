# 07 — RUL Model Design

## The design decision that prevents demo disasters

**RUL = cycles until SoH reaches 60% (second-life EOL), counted from now.** Not 70%. A retired EV pack arrives at 70–85% SoH — RUL-to-70% would be near zero or negative for half the fleet, producing "Grade B, RUL 0.2 years" absurdities on stage. Second-life applications run to ~60%; the 60% convention makes every grade's RUL meaningful. (Already consistent with judge_attacks #13: "second-life EOL (60%) is separately configurable.")

## Labeling (because NASA cells stop near 70%)

Per cell: fit a degradation curve to the smoothed capacity series — try linear and double-exponential, keep the better in-sample fit — and extrapolate to the 60% crossing. `rul_k = crossing_cycle − k`. This is declared methodology, not a trick: the model card states "RUL labels below 70% SoH are curve-extrapolated." A judge who finds this in the README respects it; one who finds it hidden does not.

## Spec

| Aspect | Decision |
|---|---|
| Models | 3 × `HistGradientBoostingRegressor`, `loss="quantile"`, alpha = 0.1 / 0.5 / 0.9 |
| Input | same 14-feature dict as SoH (one feature pipeline, two heads) |
| Native output | `rul_cycles` = q50, int, **clipped to [0, RUL_CYCLES_MAX = 2400]** (audit fix M2) |
| Interval | `rul_low/high` from q10/q90 — **sort the three quantile outputs** before use (quantile crossing happens with small data) |
| Post-processing | cycles clamped [0, 2400] → years = `rul_cycles / 300` ≤ 8.0 **by construction** — the displayed years and the energy math (which consumes rul_cycles) can no longer diverge; `rul_low ≤ rul_years ≤ rul_high` enforced |

## Cycles → years conversion logic

`rul_years = rul_cycles / 300`, where **300 cycles/year** = 2W fleet duty (~25 full-equivalent cycles/month) from `shared/constants.py` — the same constant the impact math uses (`remaining_cycles = rul_years × 300` in docs/06 — round-trips exactly because it's one constant). The assumption is printed in the UI tooltip and on the slide; in production it becomes a per-operator duty-cycle parameter. The 8-year display clamp exists because "scooter battery, 11 years" is the kind of number that loses a Q&A — clamping is honest when the interval is shown.

## What feeds on RUL

`confidence.py` (interval spread) · `grade.py` (RUL floor for S-grade) · doc 06 impact math (`energy_unlocked_mwh`) · the Life Story and Knee Alarm features. RUL is the single most-consumed number in the system — its interval discipline is why the rest is credible.
