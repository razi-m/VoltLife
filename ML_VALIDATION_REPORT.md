```
============================================
VOLTLIFE ML VALIDATION REPORT
Validator: Claude Opus 4.8 (Senior ML Validation Engineer)
Phase: 2 — ML Subsystem Validation
Date: 2026-06-13
Method: static inspection + empirical execution of every mandated test case
============================================
```

> Scope note: validated the `ml/` subsystem on disk. Banned-model scan run across all `*.py`. All scored test cases were executed live against `models/model_v1.pkl`, not assumed.

---

**SECTION 1 — FILE STRUCTURE COMPLIANCE**
Score: 10/10 · Status: PASS
Findings: All required paths present — `data/raw/`, `data/parsed/`, `models/model_v1.pkl`, `models/metrics_v1.json`, and all 15 modules (`parse_nasa.py, parse_calce.py, features.py, labels.py, train.py, evaluate.py, predict.py, confidence.py, grade.py, recommend.py, explain.py, volt_ai.py, generate_fleet.py, shared_constants.py, requirements.txt`). `tests/` contains `test_ml.py` (14 tests, non-empty). Exactly one pickle (`models/model_v1.pkl`) — no loose pickles. Only extra file is `__init__.py` (required for `from ml.predict import predict` packaging) — benign.

**SECTION 2 — FEATURE PIPELINE COMPLIANCE**
Score: 9/10 · Status: PASS
Findings: All 14 canonical features implemented in exact order (`shared_constants.py:12-27`, `features.py`); no additions/substitutions. Missing features handled gracefully — `features_dict_to_vector()` returns `(vector, missing_features)` and never crashes (verified: 13-missing input returns a valid result). Normalized to [0,1] via `normalize_vector()` against the OOD envelope. Extraction deterministic. Units documented in comments. Minor (−1): explicit *expected ranges* per feature are not all stated.

**SECTION 3 — SOH MODEL COMPLIANCE**
Score: 10/10 · Status: PASS
Findings: `HistGradientBoostingRegressor` only (`train.py:43-44`). **No banned models anywhere.** Input = 14 features. Post-processing present and correct: `round(float(_clamp(pred,0,100)),1)` (`predict.py:61`). LOCO via `LeaveOneGroupOut` (`train.py:94`); no random split. Saved to `models/model_v1.pkl`.

**SECTION 4 — RUL MODEL COMPLIANCE**
Score: 10/10 · Status: PASS
Findings: Three quantile models Q10/Q50/Q90 = `HistGradientBoostingRegressor(loss="quantile")` (`train.py:47-48,100-102`). `rul_years = rul_cycles/300` (`predict.py`, `CYCLES_PER_YEAR=300`). Hard clamps enforced: `rul_cycles∈[0,2400]`, `rul_years∈[0,8]`, `rul_low/high∈[0,8]` with `rul_low≤rul_years≤rul_high` (`predict.py:71-83`). Verified under extreme inputs (0, +1e6, −1e6) — no out-of-range values. All three stored in the bundle.

**SECTION 5 — MODEL BUNDLE COMPLIANCE**
Score: 9/10 · Status: PASS
Findings: Bundle loads cleanly. All required keys present: `soh_model, rul_q10, rul_q50, rul_q90, feature_keys, metrics, ood_envelope, shap_background, version("v1.0.0"), trained_on`. `feature_keys` == 14 canonical in order. `shap_background` is an `ndarray` (n×14). `ood_envelope` has min/max (plus mean/std). No loose pickles. Minor (−1): bundle carries extra keys (`rul_conformal_margin`) and envelope has extra `mean/std` vs the "exactly" list — additive and benign (needed for confidence + RUL calibration).

**SECTION 6 — CONFIDENCE ENGINE COMPLIANCE**
Score: 10/10 · Status: PASS
Findings: Returns only `high/medium/low`. **All 5 test cases pass:** all-present→high; 2-missing→medium; 5-missing→low; z-score 8.0→low; low-confidence battery is not auto-deployed (routes to inspection). OOD via per-feature z-score against the training envelope (`confidence.py:max_ood_z`). Low confidence never suppressed.

**SECTION 7 — GRADE ENGINE COMPLIANCE**
Score: 10/10 · Status: PASS
Findings: **All 8 test cases pass:** SoH 95/high/low-thermal/RUL5→S; 85→A; 75→B; 65→C; 55→D; SoH85+max_temp60→D; SoH85+ir_growth65→D; Grade D returns `blocked=True`, route="Certified Recycler". Hard safety override is checked FIRST and is non-overridable, clearly documented (`grade.py:6-8,43-46`).

**SECTION 8 — RECOMMENDATION ENGINE COMPLIANCE**
Score: 6/10 · Status: WARNING
Findings: Deterministic, **no ML model inside** `recommend.py` (verified). Grade D → Certified Recycler selected only (PASS); low-confidence → "Inspection Required" (PASS); Grade C → Street Lighting eligible (PASS); reasoning string present and readable (PASS).
**FAIL — Test 1:** Grade S battery does NOT surface **EV Charging Buffer** in top_3. Live ranking for S/SoH95/RUL6: `Street Lighting 0.835, Rural Microgrid 0.778, Solar Storage 0.71, Telecom Tower 0.705, Industrial Backup 0.667, EV Charging Buffer 0.565` — EV ranks **last**. Root cause: the score uses *headroom over the destination minimum* (`recommend.py:27-28`), so a premium destination (EV, min_soh 90) gets a near-zero SoH score for a 95% battery while low-tier destinations (min_soh 60) score high. The premium battery is steered to the lowest-tier site — a demo-visible correctness problem affecting all S/A batteries. (−3 test failure, −1 systemic ranking concern.)

**SECTION 9 — SHAP EXPLAINABILITY COMPLIANCE**
Score: 7/10 · Status: WARNING
Findings: SHAP is the only method (`shap.TreeExplainer` on the SoH model, background from the bundle). **No LLM used** — confirmed by grep; the only "LLM" tokens are docstring comments asserting "NO LLM calls". Deterministic (same input → identical reasons). Positive & negative signals populated; top factors non-empty; background loads. No raw feature *keys* in reasons.
**FAIL — Test 2:** reason strings DO contain **numeric values**, e.g. `"High capacity fade (15.5%) — significant ageing"`, `"High discharge efficiency (0.953)"` (`explain.py:24-66` templates embed `{v:.1f}`). The spec requires reasons contain no numeric values (its own examples have none). (−3.)

**SECTION 10 — VOLT AI LAYER COMPLIANCE**
Score: 10/10 · Status: PASS
Findings: **All 5 test cases pass.** Volt AI is additive — it reads the result and returns 5 narrative strings (`executive_summary, assessment_narrative, deployment_justification, impact_narrative, human_readable_report`); it does NOT mutate `soh_pct/rul_*/confidence/grade/score` (verified unchanged). No LLM call (template-based, `volt_ai.py`). Deterministic. Grade D impact narrative reflects recycling.

**SECTION 11 — OUTPUT CONTRACT COMPLIANCE**
Score: 6/10 · Status: WARNING
Findings: All 9 frozen fields present with correct types (`soh_pct` float, `rul_cycles` int, etc.); `confidence`∈{high,medium,low}; `grade`∈{S,A,B,C,D}; `rul_years∈[0,8]`; `rul_cycles∈[0,2400]`; `reasons` is a list; JSON-serializable.
Issues:
- **Extra fields** — `predict()` adds `explanation` and `volt_ai` beyond the frozen 9-field contract (`predict.py:95,150`). The spec says "No extra fields added". NOTE: the backend's own `app/schemas/ml.py::AssessmentResult` **requires** `explanation`, so the validation prompt's frozen contract and the backend contract conflict — must be reconciled before integration. (−3)
- **`top_3` length not always 3** — Grade D returns a single-item `top_3` (`recommend.py:43`). Section 11 says "exactly 3"; Section 8 Test 2 *requires* D to be recycler-only. The two sections contradict. (−1)
- **Edge Test 3 partial** — a contradictory all-zero input with `capacity_fade_pct=100` yields `soh_pct=56.5, rul_cycles=523` rather than the expected `soh≈0, rul_cycles=0` (model is not forced to rul=0 at the SoH floor). grade=D ✓, confidence=low ✓. (−... noted, minor)

**SECTION 12 — TRAINING PIPELINE COMPLIANCE**
Score: 10/10 · Status: PASS
Findings: LOCO (`LeaveOneGroupOut`), **no random split**, no cross-cell leakage (whole cells held out; features at cutoff K only see history ≤ K). Hackathon mode (fixed hyperparameters, no grid search). `metrics_v1.json` + `model_v1.pkl` generated. Synthetic fallback works (`train.py:55-61` auto-generates NASA-schema data when `cells.json` absent). Metrics meet all thresholds: **SoH MAE 0.176 (<5)**, **R² 0.998 (>0.85)**, **RUL coverage 0.85 (>0.80)**; CALCE cross-dataset SoH MAE 0.21.

**SECTION 13 — DEMO FLEET COMPLIANCE**
Score: 10/10 · Status: PASS
Findings: Exactly **847** batteries. Distribution **S 4.4% / A 15.6% / B 35.1% / C 31.4% / D 13.6%** — all within tolerance. Every battery has a complete assessment record (grade + soh + full prediction). OEMs: Ola, Ather, Tata, TVS. Geography: 15 Indian cities with lat/lng. Loads without errors.

---
```
============================================
SCORING SUMMARY
============================================
```

| Section | Description | Max | Score |
|---|---|---|---|
| 1 | File Structure | 10 | 10 |
| 2 | Feature Pipeline | 10 | 9 |
| 3 | SoH Model | 10 | 10 |
| 4 | RUL Model | 10 | 10 |
| 5 | Model Bundle | 10 | 9 |
| 6 | Confidence Engine | 10 | 10 |
| 7 | Grade Engine | 10 | 10 |
| 8 | Recommendation Engine | 10 | 6 |
| 9 | SHAP Explainability | 10 | 7 |
| 10 | Volt AI Layer | 10 | 10 |
| 11 | Output Contract | 10 | 6 |
| 12 | Training Pipeline | 10 | 10 |
| 13 | Demo Fleet | 10 | 10 |
| | **TOTAL** | **130** | **117** |
| | **PERCENTAGE** | **100%** | **90.0%** |

```
============================================
ISSUES REGISTER
============================================
```

| # | Severity | Sec | File:Line | Issue | Fix Required |
|---|---|---|---|---|---|
| 1 | HIGH | 8 | recommend.py:27-34 | Grade S battery ranks **EV Charging Buffer last** (0.565); not in top_3. Headroom-over-min_soh scoring inverts intent — premium batteries steered to low-tier sites. Fails Sec 8 Test 1. | Reward grade/SoH *tier match* (not just headroom) so premium destinations surface for premium batteries. |
| 2 | MEDIUM | 9 | explain.py:24-66 | Reason strings embed numeric values (e.g. "(15.5%)"). Fails Sec 9 Test 2. | Remove numerics from reason labels (spec examples are number-free). |
| 3 | MEDIUM | 11 | predict.py:95,150 | `predict()` returns extra `explanation` + `volt_ai` fields vs frozen contract. But backend `AssessmentResult` *requires* `explanation` — contracts conflict. | Reconcile the frozen contract with the backend schema before integration; decide canonical shape. |
| 4 | LOW | 11/8 | recommend.py:43 | `top_3` has 1 item for Grade D (Sec 11 says exactly 3; Sec 8 requires recycler-only). Spec sections contradict. | Clarify spec; pad or document D as a deliberate single-item route. |
| 5 | LOW | 11 | predict.py:61-83 | Edge SoH≈0 (contradictory input) → soh 56.5 / rul_cycles 523, not 0/0. | Optionally force rul=0 when SoH ≤ EOL floor. |
| 6 | LOW | 5/12 | train.py:89-90,158 | Bundle/envelope/metrics carry extra keys vs "exact" lists (additive, benign). | None required; document. |
| 7 | LOW | 2 | shared_constants.py:12-27 | Features documented with units but not explicit expected ranges. | Add expected ranges in comments. |

```
============================================
FINAL VERDICT
============================================
```

**CONDITIONAL PASS — MINOR FIXES REQUIRED**

Score: **117/130 (90.0%)** — exactly on the READY/CONDITIONAL boundary.

Reason: The subsystem is architecturally clean and substantially correct — **zero banned models** (only `HistGradientBoostingRegressor` + SHAP), **LOCO with no leakage**, **Grade-D hard safety override verified across all 8 cases**, bundle loads with all required keys, all metric thresholds met, and the 847-battery fleet is complete and correctly distributed. However the numeric score sits at the threshold *because of one HIGH issue* — the recommendation engine ranks the premium destination (EV Charging Buffer) last for premium (Grade S) batteries, which fails a documented test case and would be visible to judges — plus two MEDIUM issues (numeric values in SHAP reason strings; output carries extra fields whose status conflicts between the frozen contract and the backend's required `AssessmentResult`). None are CRITICAL; the output contract core and Grade-D safety are intact.

Next Step:
> Fix Issues #1–#3 (recommendation tier-matching, number-free reason strings, reconcile the explanation field between the frozen contract and the backend schema). Re-run this validation. Proceed to Phase 3 — Backend ↔ ML Integration — only after re-validation clears the recommendation and contract findings.
```
============================================
```
