# 09 — Explainability Strategy

Two audiences, one artifact: judges get plain English; ML-literate judges get the SHAP drill-down underneath. Both come from the same computation — no parallel explanation systems.

## Pipeline (`explain.py`)

1. SHAP explainer (fallback chain per 04_*) initialized **once at model load** with a fixed background sample (~100 training rows, shipped in the bundle) — deterministic, fast, identical across calls.
2. Per battery: SHAP values on the SoH model → rank features by |value| → take top 3–6.
3. Each becomes `{"feature", "value" (raw input), "impact" ("+" pushes health up / "−" down), "shap" (float), "label" (templated English)}` → stored as `assessments.explanation_json` (drill-down) and `reasons` = top-3 labels (cards, WS).

## Template table (extends docs/05; binding for `explain.py`)

| (feature, impact) | Label |
|---|---|
| avg_temp_c, + | "Low thermal stress (avg {v:.0f}°C)" |
| avg_temp_c, − | "High operating temperature (avg {v:.0f}°C)" |
| thermal_stress_hours, − | "{v:.0f} hours above 40°C — cumulative heat damage" |
| fade_acceleration, − | "Capacity fade accelerating — degradation knee detected" |
| fade_rate, + | "Slow, stable degradation trend" |
| fade_rate, − | "Capacity declining faster than fleet norm" |
| cycle_count, + | "Moderate cycle count ({v:.0f} cycles)" |
| cycle_count, − | "High cycle count ({v:.0f} cycles)" |
| internal_resistance_mohm / ir_growth_pct, − | "Internal resistance up {v:.0f}% from baseline" |
| ir_growth_pct, + | "Internal resistance near factory baseline" |
| voltage_variance, + | "Healthy voltage profile under load" |
| voltage_variance, − | "Unstable voltage profile — possible cell imbalance" |
| voltage_slope, − | "Steepening discharge curve" |
| cv_phase_fraction, − | "Extended constant-voltage charging — aging marker" |
| charge_efficiency, − | "Coulombic efficiency declining — side reactions" |
| discharge_efficiency, + | "High round-trip energy efficiency" |
| capacity_fade_pct, ± | "Capacity at {100−v:.0f}% of rated" |

Coverage rule: every (feature, sign) pair has a template; unknown pairs fall back to "{feature} {direction} fleet norm" — never an empty reason, never a raw feature name on a judge-facing card.

## Judge drill-down path

DecisionCard shows 3 labels → BatteryDetail's ExplainabilityPanel shows signed horizontal bars (label + shap magnitude) → if a judge pushes further, the `explanation_json` is raw SHAP values on screen via the panel's expanded state, and `explain.py` + background-sample methodology is open in the repo. Three depths, zero improvisation.

## Honesty guardrails (judge_attacks #8)

SHAP on correlated features ≠ causal attribution — labels are phrased as observations ("high temperature", "knee detected"), not causes ("temperature caused 7% loss"). Templates were sanity-checked against electrochemical priors; if a SHAP sign ever contradicts physics for a feature (it can, with correlation), the template renders the *observation* which remains true. Deterministic explanations (fixed background, fixed seed) mean the same battery always tells the same story — rehearsal-safe.
