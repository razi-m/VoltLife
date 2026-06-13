# 01 — ML Output Contract (BINDING for Antigravity)

The ML subsystem exposes **three pure functions**. `assess()` is already bound by `docs/integration_validation.md` §3 and MUST NOT change shape. The composite `evaluate_battery()` produces the full response format (below) by chaining assess → recommend. **API contracts (docs/04) are frozen — ML adapts to them; nothing here changes the wire.**

## 1. `assess(features: dict) -> AssessmentResult`

Input: dict whose keys are exactly the 14 canonical feature keys (03_feature_spec.md). Missing values allowed as `None`/NaN (model handles natively); unknown keys → `ValueError`.

| Field | Type | Range / values | Validation rule |
|---|---|---|---|
| `soh_pct` | float | 0.0–100.0, 1 decimal | clip post-prediction; never NaN |
| `rul_cycles` | int | **0–2400** | native model output (cycles to 60% SoH); clip to [0, RUL_CYCLES_MAX=2400] (= RUL_YEARS_MAX 8.0 × CYCLES_PER_YEAR 300 — audit fix M2: keeps energy math and displayed years consistent) |
| `rul_years` | float | 0.0–8.0, 1 decimal | `rul_cycles / CYCLES_PER_YEAR` (300, from shared/constants.py); ≤ 8.0 by construction given the cycles clamp |
| `rul_low` / `rul_high` | float | 0 ≤ low ≤ rul_years ≤ high | from q10/q90 models; enforce ordering by sorting |
| `grade` | str | `"S" "A" "B" "C" "D"` | wire encoding; `D` renders as **Recycle** (10_grading_strategy.md) |
| `confidence` | str | `"high" "medium" "low"` | three values on the wire; demo policy in 08_confidence_strategy.md |
| `explanation` | list[dict] | 3–6 entries | `{"feature": str, "value": float, "impact": "+"/"-", "shap": float, "label": str}` |
| `reasons` | list[str] | exactly 3 | `[e["label"] for e in explanation[:3]]` |

`rul_cycles` is **additive** — it does not appear in the frozen wire API (docs/04); it is available to the backend and used by the impact math (`remaining_cycles`) and the composite response.

## 2. `recommend(assessment, battery_meta, sites) -> RecommendationResult`

Pure scoring engine (NOT a model — see 11_deployment_recommendation_strategy.md). Backend's `services/deployment.py` supplies live site state and persists results.

| Field | Type | Rule |
|---|---|---|
| `recommendations` | list[dict], 1–3 | `{"destination": str, "site_id": int, "score": int 0–100, "factors": [3 strings]}` — descending score |
| `selected_destination` | str | == `recommendations[0]["destination"]` after capacity check |
| `selected_site_id` | int | FK into sites |
| `energy_unlocked_mwh` | float ≥ 0 | doc 06 formula; **0 for grade D** |
| `carbon_saved_kg` | float ≥ 0 | doc 06 formula; **0 for grade D** |

Hard rule encoded here, not in the caller: `grade == "D"` → recommendations contain recyclers only, exactly 1 entry.

## 3. `evaluate_battery(battery_meta, features, sites) -> dict` (composite)

The full ML response format, assembled from §1 + §2:

```json
{
  "battery_id": "BAT-001",
  "soh_pct": 82.0,
  "rul_cycles": 1290,
  "rul_years": 4.3,
  "confidence": "high",
  "grade": "A",
  "reasons": ["Low thermal stress (avg 31°C)", "Stable voltage profile under load", "Moderate cycle count (412)"],
  "recommendations": [
    {"destination": "Bhadla Solar Park Storage, RJ", "site_id": 3, "score": 87, "factors": ["..."]},
    {"destination": "Hyderabad ORR Charging Hub, TS", "site_id": 9, "score": 81, "factors": ["..."]},
    {"destination": "Gaya Rural Microgrid, BR", "site_id": 5, "score": 74, "factors": ["..."]}
  ],
  "selected_destination": "Bhadla Solar Park Storage, RJ"
}
```

**Field mappings to the frozen wire (docs/04):**

| Composite field | Wire location |
|---|---|
| `battery_id` ("BAT-001") | = ingestion `external_ref`; wire uses integer `battery_id` + `aadhaar_id` — composite keeps external_ref for operator readability |
| `rul_years` + assess `rul_low/high` | WS `rul_range: [low, high]` |
| `recommendations` (top-3) | `deployments.reasoning_json` → powers the counterfactual "Why not?" panel (innovation #4) — ranks 2–3 ARE the runner-ups |
| `selected_destination` | WS `deployment.site_name` |
| `score` (0–100 int) | `round(raw_score × 100)`; raw 0–1 float stored in `deployments.score` |

## 4. Global validation rules (enforced in predictor, tested in 14_demo_validation.md)

Never raise out of `assess()`/`recommend()` in pipeline context — the backend wraps per-battery try/except (docs/08), but the functions themselves must return clipped, ordered, enum-valid values for any plausible input. NaN/Inf in any output = bug, caught by the QA harness, never shipped to the wire.
