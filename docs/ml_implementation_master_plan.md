# VOLTLIFE — ML IMPLEMENTATION MASTER PLAN
**Project:** VoltLife — AI-Powered Battery Intelligence Platform
**Phase:** 2 — ML Subsystem
**Owner:** Razi
**Status:** In Progress
**Last Updated:** 2026-06-13

---

## CRITICAL — BEFORE YOU BEGIN

1. Read the entire repository before making any changes
2. Read every file in the local VoltLife working directory
3. Read the backend implementation and locate the ML integration seam
4. Read all files in `ml-plan/` before writing any code
5. Ask all necessary clarifying questions before generating anything
6. Do not assume any file contents
7. If anything is undefined or ambiguous — stop and ask
8. Do not proceed if the repository or local folder is inaccessible

---

## PRIMARY OBJECTIVE

Build VoltLife's Battery Intelligence Layer as a standalone ML subsystem.

The ML subsystem must produce:

- State of Health (SoH)
- Remaining Useful Life (RUL)
- Confidence Level
- Battery Grade
- Deployment Recommendation
- Explainability Output

The frontend already exists. Do not modify it.
The backend already exists. Do not modify it.
Your responsibility is ONLY the ML subsystem.

---

## OUTPUT CONTRACT — FROZEN

Every prediction must return exactly this structure.
This contract is frozen. Do not modify under any circumstance.
Backend integration depends on this exact structure.
Any deviation breaks the integration seam.

```json
{
  "soh_pct": float,
  "rul_years": float,
  "rul_cycles": int,
  "rul_low": float,
  "rul_high": float,
  "confidence": "high|medium|low",
  "grade": "S|A|B|C|D",
  "recommendation": {
    "top_3": [],
    "selected": "",
    "score": float,
    "reasoning": ""
  },
  "reasons": []
}
```

---

## ABSOLUTE CONSTRAINTS

```
DO NOT redesign the architecture
DO NOT introduce alternative models
DO NOT introduce fallback models
DO NOT introduce Random Forest
DO NOT introduce XGBoost
DO NOT introduce LightGBM
DO NOT introduce CatBoost
DO NOT introduce neural networks
DO NOT introduce LSTMs
DO NOT introduce transformers
DO NOT create parallel training pipelines
DO NOT modify API contracts
DO NOT modify backend contracts
DO NOT modify frontend contracts
DO NOT use LLMs for explainability
DO NOT use random train/test split (use LOCO only)
```

The architecture below is final. No deviations permitted.

---

## APPROVED ARCHITECTURE

```
Telemetry
    ↓
Feature Extraction
    ↓
SoH Model
    ↓
RUL Models (Q10 / Q50 / Q90)
    ↓
Confidence Engine
    ↓
Grade Engine
    ↓
Recommendation Engine
    ↓
Explainability Engine (SHAP)
    ↓
Volt AI Layer
    ↓
Backend Integration
```

---

## ENVIRONMENT

```
Python: 3.10+
```

**Pinned dependencies (requirements.txt):**
```
scikit-learn==1.3.2
numpy==1.24.3
pandas==2.0.3
joblib==1.3.2
scipy==1.11.4
shap==0.43.0
pyserial==3.5
```

> **Note on pyserial:** Required for UART/Serial BMS hardware
> integration (ESP32 + INA219 + DS18B20). Hardware phase is Phase 7
> but the dependency must be listed now.

---

## DIRECTORY STRUCTURE

Create and maintain exactly this structure:

```
ml/
├── data/
│   ├── raw/
│   └── parsed/
├── models/
│   ├── model_v1.pkl
│   └── metrics_v1.json
├── tests/
├── parse_nasa.py
├── parse_calce.py
├── features.py
├── labels.py
├── train.py
├── evaluate.py
├── predict.py
├── confidence.py
├── grade.py
├── recommend.py
├── explain.py
├── volt_ai.py
├── generate_fleet.py
├── shared_constants.py
└── requirements.txt
```

---

## DATASETS

### Primary — NASA Battery Dataset
**Purpose:**
- Training
- Feature Engineering
- SoH Prediction
- RUL Prediction

**Parser:** `parse_nasa.py`

### Secondary — CALCE Battery Dataset
**Purpose:**
- Validation
- Generalization Testing

**Parser:** `parse_calce.py`

### Oxford Dataset
Optional. Must not block implementation.

### Synthetic Fallback
If datasets are not yet downloaded — generate synthetic data
that matches the parsed NASA schema exactly.
`train.py` must run on synthetic data immediately without errors.

---

## FEATURE SPECIFICATION

The system must use exactly these 14 canonical features.
No additions. No substitutions. No removals.

| # | Feature | Description | Unit |
|---|---|---|---|
| 1 | `cycle_count` | Total charge/discharge cycles | cycles |
| 2 | `capacity_fade_pct` | Capacity loss from nominal | % |
| 3 | `fade_rate` | Capacity fade per cycle | fraction/cycle |
| 4 | `fade_acceleration` | Rate of change of fade_rate | fraction/cycle² |
| 5 | `avg_temp_c` | Average operating temperature | °C |
| 6 | `max_temp_c` | Peak temperature recorded | °C |
| 7 | `thermal_stress_hours` | Hours above 45°C | hours |
| 8 | `internal_resistance_mohm` | Internal resistance | mOhm |
| 9 | `ir_growth_pct` | IR growth from baseline | % |
| 10 | `cv_phase_fraction` | Fraction of charge in CV phase | fraction |
| 11 | `voltage_slope` | Rate of voltage change over cycles | V/cycle |
| 12 | `voltage_variance` | Variance in voltage readings | V² |
| 13 | `charge_efficiency` | Charge energy in vs out ratio | fraction |
| 14 | `discharge_efficiency` | Discharge energy ratio | fraction |

**Feature handling requirements:**
- Handle missing features gracefully — never crash
- Return `missing_features` list for confidence engine
- Normalize all features to 0-1 range before model input
- All extraction must be deterministic

---

## SOH MODEL

**Model:** `HistGradientBoostingRegressor`
**Target:** `soh_pct`
**Input:** 14 canonical features
**Output:** 0.0 — 100.0

**Post-processing (apply in this order):**
```python
soh_pct = np.clip(prediction, 0, 100)
soh_pct = round(soh_pct, 1)
```

This is the only SoH model. No alternatives.

---

## RUL MODEL

Build exactly three quantile models:

| Model | Quantile | Purpose |
|---|---|---|
| Q10 | 0.10 | Pessimistic lower bound |
| Q50 | 0.50 | Median prediction (primary) |
| Q90 | 0.90 | Optimistic upper bound |

**Model:** `HistGradientBoostingRegressor`
**Loss:** `quantile`
**Target:** `rul_cycles`

**Output fields:**
```
rul_cycles  → Q50 prediction (primary)
rul_years   → rul_cycles / 300 (avg 300 cycles/year)
rul_low     → Q10 prediction
rul_high    → Q90 prediction
```

**Hard clamps — enforce everywhere, no exceptions:**
```python
rul_years  = max(0.0, min(8.0, predicted))
rul_cycles = max(0, min(2400, predicted))
rul_low    = max(0.0, rul_low)
rul_high   = min(8.0, rul_high)
```

This is the only RUL architecture. No alternatives.

---

## TRAINING STRATEGY

**Method:** Leave-One-Cell-Out Cross Validation (LOCO)

```
For each cell C in dataset:
    Train on all cells EXCEPT C
    Validate on cell C
    Record metrics
```

**Random train/test split is strictly forbidden.**
No data leakage allowed under any condition.

**Training rows:**
Generate training rows from lifecycle cutoffs.
Features at cutoff K → Labels at cutoff K.

**Hackathon Mode (default — HACKATHON_MODE = True):**
- No grid search
- Fixed hyperparameters
- Max training time: 10 minutes

**Full Mode (post-hackathon — HACKATHON_MODE = False):**
- Grid search enabled
- Full hyperparameter optimization

---

## TARGET METRICS

Record all metrics in `models/metrics_v1.json`:

```json
{
  "version": "v1.0.0",
  "trained_on": "2026-06-13",
  "dataset": "NASA",
  "hackathon_mode": true,
  "soh": {
    "mae": float,
    "rmse": float,
    "r2": float
  },
  "rul": {
    "mae": float,
    "coverage": float
  }
}
```

**Acceptable thresholds (hackathon baseline):**
- SoH MAE < 5.0
- SoH R² > 0.85
- RUL Coverage > 0.80

---

## CONFIDENCE ENGINE — confidence.py

**Outputs:** `high` / `medium` / `low`

### Confidence Signals
- Quantile spread (Q90 - Q10)
- OOD detection (z-score against training envelope)
- Feature envelope checks
- SoH divergence checks
- Missing feature count

### Confidence Rules

| Condition | Level |
|---|---|
| All features present + in-distribution + low spread | `high` |
| 1-3 features missing OR mild OOD (z-score 2-3) | `medium` |
| 4+ features missing OR severe OOD (z-score > 3) | `low` |
| Quantile spread > threshold | `medium` or `low` |
| Anomalous input detected | `low` |

### Confidence Enforcement Rules
- Low confidence batteries **cannot** auto-deploy
- Low confidence batteries **must** route to inspection
- Never suppress low confidence output
- Confidence level must always be present in output

---

## GRADE ENGINE — grade.py

**Supported grades:** S / A / B / C / D

> Grade D renders as "Recycle" in the frontend.

### Grade Thresholds

| Grade | Primary Condition | Additional Requirements |
|---|---|---|
| S | SoH ≥ 90% | High confidence + Low thermal stress + RUL ≥ 4 years |
| A | SoH ≥ 80% | — |
| B | SoH ≥ 70% | — |
| C | SoH ≥ 60% | — |
| D | SoH < 60% OR safety trigger | Hard safety override |

### Grade D Safety Triggers — Hard Override

Grade D triggers if ANY of these conditions are true:

```python
soh_pct < 60.0
OR max_temp_c > 55.0          # °C
OR ir_growth_pct > 60.0       # %
```

**Grade D behavior:**
- Blocks all deployment — cannot be overridden by any logic
- Deployment planner receives `"status": "blocked"`
- Routes directly to Certified Recycler
- Safety rule — no exceptions
- Must be clearly documented in code comments

---

## DEPLOYMENT RECOMMENDATION ENGINE — recommend.py

> This is NOT an ML model.
> This is a transparent deterministic scoring engine.

### Inputs
- SoH
- RUL
- Grade
- Confidence
- Capacity
- Location
- Site Metadata

### Outputs

```json
{
  "top_3": ["destination_1", "destination_2", "destination_3"],
  "selected": "destination_1",
  "score": float,
  "reasoning": "human readable string"
}
```

### Supported Destinations

| Destination | Min Grade | Min SoH | Notes |
|---|---|---|---|
| Solar Storage | B | 70% | High cycle tolerance |
| Industrial Backup | A | 80% | Reliability critical |
| Rural Microgrid | B | 70% | High impact, lower demand |
| Telecom Tower | A | 80% | Uptime critical |
| EV Charging Buffer | S | 90% | Peak performance needed |
| Street Lighting | C | 60% | Low demand application |
| Certified Recycler | D | any | Grade D mandatory route |

### Logic
- Score each destination against battery profile
- Rank by score
- Return top 3 + selected (highest score)
- Generate reasoning string explaining the selection
- Low confidence batteries route to inspection — not deployment

---

## EXPLAINABILITY ENGINE — explain.py

**Method:** SHAP (SHapley Additive exPlanations)
**Source of truth:** ML model — not Volt AI

### Requirements
- Generate SHAP values for every prediction
- Extract top factors (positive and negative)
- Generate human-readable reason strings
- Outputs must be deterministic
- Do not use LLMs for explainability
- SHAP background dataset stored in `model_v1.pkl`

### Outputs

```json
{
  "top_factors": ["factor_1", "factor_2", "factor_3"],
  "positive_signals": ["signal_1", "signal_2"],
  "negative_signals": ["signal_1"],
  "reasons": ["reason_1", "reason_2", "reason_3"]
}
```

### Reason String Examples
```
"Low capacity fade detected — battery aging within normal range"
"Stable voltage profile — consistent charge/discharge behavior"
"Normal thermal behavior — no heat stress events recorded"
"High cycle count — approaching end of operational life"
"Elevated internal resistance — increased degradation signal"
"Thermal stress events recorded — reduced deployment suitability"
```

---

## VOLT AI LAYER — volt_ai.py

> Volt AI is an explanation layer ONLY.
> Volt AI is NOT a prediction layer.

### Volt AI Must NEVER Modify
- `soh_pct`
- `rul_cycles`
- `rul_years`
- `confidence`
- `grade`
- `recommendation score`

ML remains the source of truth for all predictions.

### Volt AI Only Generates

```json
{
  "executive_summary": "string",
  "assessment_narrative": "string",
  "deployment_justification": "string",
  "impact_narrative": "string",
  "human_readable_report": "string"
}
```

### Requirements
- Deterministic outputs from ML inputs
- No LLM calls
- Template-based generation from grade + confidence + SHAP factors
- Same input = same output always

---

## MODEL STORAGE

Create exactly one model artifact:

**File:** `models/model_v1.pkl`

**Bundle must contain:**

```python
{
  "soh_model": HistGradientBoostingRegressor,
  "rul_q10": HistGradientBoostingRegressor,
  "rul_q50": HistGradientBoostingRegressor,
  "rul_q90": HistGradientBoostingRegressor,
  "feature_keys": [...],         # ordered list of 14 features
  "metrics": {...},              # training metrics
  "ood_envelope": {...},         # min/max per feature from training
  "shap_background": np.ndarray, # background dataset for SHAP
  "version": "v1.0.0",
  "trained_on": "2026-06-13"
}
```

No multiple model files. No loose pickle files.
One artifact only.

---

## DEMO FLEET — generate_fleet.py

Generate exactly 847 batteries with this grade distribution:

| Grade | Target % | Target Count |
|---|---|---|
| S | ~5% | ~42 |
| A | ~15% | ~127 |
| B | ~35% | ~297 |
| C | ~30% | ~254 |
| D | ~15% | ~127 |

**Requirements:**
- Every dashboard screen must be populated
- No empty charts
- No empty tables
- No placeholder records
- All 847 batteries must have complete assessment records
- Geographically distributed across India
- Manufacturers: Ola, Ather, Tata, TVS proportionally distributed

---

## IMPLEMENTATION ORDER

Follow this sequence strictly:

| Phase | Task | File |
|---|---|---|
| 1 | NASA Parser | `parse_nasa.py` |
| 2 | Feature Engineering | `features.py` |
| 3 | Label Generation | `labels.py` |
| 4 | SoH Model Training | `train.py` |
| 5 | RUL Quantile Models | `train.py` |
| 6 | Confidence Engine | `confidence.py` |
| 7 | Grade Engine | `grade.py` |
| 8 | Recommendation Engine | `recommend.py` |
| 9 | SHAP Explainability | `explain.py` |
| 10 | Volt AI Layer | `volt_ai.py` |
| 11 | Demo Fleet Generation | `generate_fleet.py` |
| 12 | Backend Integration Prep | `predict.py` |
| 13 | Validation Suite | `tests/` |

---

## TRAINING COMMANDS

```bash
# Parse NASA dataset
python parse_nasa.py --input data/raw/nasa --output data/parsed/

# Parse CALCE dataset
python parse_calce.py --input data/raw/calce --output data/parsed/

# Train all models
python train.py --data data/parsed/ --mode hackathon

# Evaluate
python evaluate.py --model models/model_v1.pkl

# Generate demo fleet
python generate_fleet.py --count 847 --output data/fleet.json

# Run validation suite
python -m pytest tests/
```

---

## BACKEND INTEGRATION REQUIREMENT

Phase 3 integration must require only:

```python
# Replace mock in backend with:
from ml.predict import predict
```

- No schema changes
- No API changes
- No database changes
- No output contract changes

Design every interface with this constraint from day one.

---

## COMPLETION CRITERIA

The ML phase is complete only when every item is checked:

- [ ] NASA Dataset Parsed
- [ ] CALCE Dataset Parsed (or skipped with note)
- [ ] Features Generated (all 14 canonical features)
- [ ] Labels Generated
- [ ] LOCO Validation Complete
- [ ] SoH Model Trained (`HistGradientBoostingRegressor`)
- [ ] RUL Models Trained (Q10, Q50, Q90)
- [ ] Confidence Engine Working
- [ ] Grade Engine Working (Grade D safety override verified)
- [ ] Recommendation Engine Working
- [ ] SHAP Explainability Working
- [ ] Volt AI Layer Working
- [ ] Demo Fleet Generated (847 batteries, correct distribution)
- [ ] Backend Integration Ready (`predict.py` callable)
- [ ] `metrics_v1.json` Generated
- [ ] `model_v1.pkl` Generated
- [ ] All tests passing in `tests/`
- [ ] Output contract verified byte-for-byte against spec
- [ ] RUL clamps enforced (verified with edge case tests)
- [ ] Grade D blocks deployment (verified with test case)

Provide a final implementation report when complete.
Then stop.
Do not perform backend integration.
Wait for explicit Phase 3 instruction.

---

## RISK REGISTER

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| NASA dataset not downloaded | Medium | High | Use synthetic fallback immediately |
| SHAP computation slow | Medium | Medium | Use small background dataset (50-100 samples) |
| LOCO validation takes too long | Medium | High | HACKATHON_MODE limits folds |
| Grade D not triggering correctly | Low | Critical | Write explicit test case before handoff |
| Output contract mismatch | Low | Critical | Validate against spec before handoff |
| model_v1.pkl bundle fails to load | Low | Critical | Validate load in tests/ before handoff |
| Missing feature crash | Medium | High | Graceful handling required in features.py |

---

## WHAT TO TELL JUDGES ABOUT DATA

> "In production VoltLife connects directly to OEM BMS APIs from
> Ola, Ather, and Tata. For this demonstration we use NASA's
> battery degradation dataset as a validated proxy for lithium-ion
> degradation patterns. The model architecture is identical to what
> would run in production."

---

*End of ML Implementation Master Plan*
*VoltLife — HackPrix 2026*
