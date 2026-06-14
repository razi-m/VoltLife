"""
VoltLife ML — shared constants (single source of truth).

Frozen values that every module in the ML subsystem imports. Nothing here may
diverge from the backend contract (app/schemas/ml.py) or the ML master plan.
"""

# ---------------------------------------------------------------------------
# Canonical feature vector — EXACTLY 14 features, fixed order. No additions,
# substitutions or removals (master plan §FEATURE SPECIFICATION).
# ---------------------------------------------------------------------------
FEATURE_KEYS = [
    "cycle_count",                 # 1  total charge/discharge cycles
    "capacity_fade_pct",           # 2  capacity loss from nominal (%)
    "fade_rate",                   # 3  capacity fade per cycle (fraction/cycle)
    "fade_acceleration",           # 4  d(fade_rate)/dcycle (fraction/cycle^2)
    "avg_temp_c",                  # 5  average operating temperature (C)
    "max_temp_c",                  # 6  peak temperature recorded (C)
    "thermal_stress_hours",        # 7  hours above 45 C
    "internal_resistance_mohm",    # 8  internal resistance (mOhm)
    "ir_growth_pct",               # 9  IR growth from baseline (%)
    "cv_phase_fraction",           # 10 fraction of charge spent in CV phase
    "voltage_slope",               # 11 rate of voltage change over cycles (V/cycle)
    "voltage_variance",            # 12 variance in voltage readings (V^2)
    "charge_efficiency",           # 13 charge energy in vs out ratio
    "discharge_efficiency",        # 14 discharge energy ratio
]
N_FEATURES = len(FEATURE_KEYS)
assert N_FEATURES == 14, "Canonical feature vector must be exactly 14 features"

# ---------------------------------------------------------------------------
# RUL / SoH constants
# ---------------------------------------------------------------------------
CYCLES_PER_YEAR = 300          # display conversion (master plan §RUL MODEL)
RUL_YEARS_MAX = 8.0            # hard clamp
RUL_CYCLES_MAX = 2400          # = RUL_YEARS_MAX * CYCLES_PER_YEAR
RUL_CYCLES_MIN = 0
SOH_EOL_PCT = 70.0             # automotive end-of-(second)-life threshold used for RUL labels

# ---------------------------------------------------------------------------
# Grade thresholds (master plan §GRADE ENGINE)
# ---------------------------------------------------------------------------
GRADE_S_SOH = 90.0
GRADE_A_SOH = 80.0
GRADE_B_SOH = 70.0
GRADE_C_SOH = 60.0
GRADE_S_MIN_RUL_YEARS = 4.0
GRADE_S_MAX_THERMAL_STRESS_H = 20.0

# Hard safety overrides -> Grade D (no override permitted)
SAFETY_SOH_FLOOR = 60.0
SAFETY_MAX_TEMP_C = 55.0
SAFETY_IR_GROWTH_PCT = 60.0

# ---------------------------------------------------------------------------
# Confidence thresholds (master plan §CONFIDENCE ENGINE)
# ---------------------------------------------------------------------------
CONF_SPREAD_MEDIUM_CYCLES = 1950.0  # Q90-Q10 spread above this -> at most medium
CONF_SPREAD_LOW_CYCLES = 3200.0     # spread above this -> low
CONF_OOD_Z_MEDIUM = 2.75            # max per-feature z-score -> medium
CONF_OOD_Z_LOW = 3.75               # max per-feature z-score -> low
CONF_MISSING_MEDIUM = 1             # 1-3 missing features -> at most medium
CONF_MISSING_LOW = 4               # >=4 missing features -> low

# ---------------------------------------------------------------------------
# Deployment destinations (master plan §DEPLOYMENT RECOMMENDATION ENGINE)
# Transparent scoring table — NOT a model.
# ---------------------------------------------------------------------------
DESTINATIONS = [
    # name,               min_grade, min_soh, demand_kwh, note
    {"name": "EV Charging Buffer", "min_grade": "S", "min_soh": 90.0, "demand_kwh": 250.0, "note": "Peak performance needed"},
    {"name": "Industrial Backup",  "min_grade": "A", "min_soh": 80.0, "demand_kwh": 400.0, "note": "Reliability critical"},
    {"name": "Telecom Tower",      "min_grade": "A", "min_soh": 80.0, "demand_kwh": 120.0, "note": "Uptime critical"},
    {"name": "Solar Storage",      "min_grade": "B", "min_soh": 70.0, "demand_kwh": 800.0, "note": "High cycle tolerance"},
    {"name": "Rural Microgrid",    "min_grade": "B", "min_soh": 70.0, "demand_kwh": 150.0, "note": "High impact, lower demand"},
    {"name": "Street Lighting",    "min_grade": "C", "min_soh": 60.0, "demand_kwh": 40.0,  "note": "Low demand application"},
    {"name": "Certified Recycler", "min_grade": "D", "min_soh": 0.0,  "demand_kwh": 0.0,   "note": "Grade D mandatory route"},
]
GRADE_RANK = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}

# Impact math (kept consistent with backend docs/06)
CO2_KG_PER_KWH = 64.5          # grid carbon offset per kWh-year of reuse (illustrative)

# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------
MODEL_VERSION = "v1.0.0"
TRAINED_ON = "2026-06-13"
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Canonical frozen OUTPUT CONTRACT (expanded — validation FIX 3).
# Reconciled with the backend (app/schemas/ml.py::AssessmentResult requires
# `explanation`). predict() returns exactly these 11 fields.
# ---------------------------------------------------------------------------
OUTPUT_CONTRACT_FIELDS = [
    "soh_pct",        # float
    "rul_years",      # float
    "rul_cycles",     # int
    "rul_low",        # float
    "rul_high",       # float
    "confidence",     # "high" | "medium" | "low"
    "grade",          # "S" | "A" | "B" | "C" | "D"
    "recommendation", # object {top_3, selected, score, reasoning}
    "reasons",        # list[str]
    "explanation",    # list[dict] {feature, value, impact, shap, label}
    "volt_ai",        # object {executive_summary, assessment_narrative, ...}
]

# ---------------------------------------------------------------------------
# CANONICAL CONTRACT RECONCILIATION (validation 2.0, ISSUE #3)
#
# Two contracts exist and they are reconciled — NOT in conflict:
#
#   ASSESSMENT_CORE_FIELDS (below) is the FROZEN cross-boundary contract. It is
#   exactly the backend `app/schemas/ml.py::AssessmentResult` (9 fields). The
#   backend constructs `AssessmentResult(**predict_output)` (pipeline.py); Pydantic
#   v2 ignores unknown keys by default, so the ML layer may return a SUPERSET.
#
#   OUTPUT_CONTRACT_FIELDS (above) is that superset: the 9 core fields PLUS two
#   ADDITIVE ML-layer extensions —
#     - `recommendation` : consumed by the deployment/marketplace path & UI
#     - `volt_ai`        : presentation-layer narratives (additive, never mutates core)
#   Both are safely ignored by AssessmentResult and required by the demo/frontend,
#   so they are retained. `explanation` and `reasons` ARE core (backend requires them).
# ---------------------------------------------------------------------------
ASSESSMENT_CORE_FIELDS = [
    "soh_pct",     # float  [0,100]
    "rul_cycles",  # int    [0,2400]
    "rul_years",   # float  [0,8]
    "rul_low",     # float  [0,8]
    "rul_high",    # float  [0,8], rul_low <= rul_years <= rul_high
    "grade",       # "S"|"A"|"B"|"C"|"D"
    "confidence",  # "high"|"medium"|"low"
    "explanation", # list[dict]
    "reasons",     # list[str]
]
# ML-layer additive extensions beyond the frozen backend core.
OUTPUT_CONTRACT_EXTENSIONS = ["recommendation", "volt_ai"]

# ---------------------------------------------------------------------------
# Expected per-feature ranges (validation 2.0, optional cleanup — DOCUMENTATION
# ONLY). These are typical operating envelopes for reference/QA; they are NOT
# used for normalization or confidence (that uses the trained ood_envelope), so
# adding them changes no behaviour. (low, high) in each feature's native unit.
# ---------------------------------------------------------------------------
FEATURE_RANGES = {
    "cycle_count":              (0.0, 2400.0),    # cycles
    "capacity_fade_pct":        (0.0, 60.0),      # %
    "fade_rate":                (0.0, 5.0e-3),    # fraction/cycle
    "fade_acceleration":        (-1.0e-4, 1.0e-4),# fraction/cycle^2
    "avg_temp_c":               (15.0, 50.0),     # C
    "max_temp_c":               (20.0, 70.0),     # C
    "thermal_stress_hours":     (0.0, 500.0),     # hours > 45C
    "internal_resistance_mohm": (15.0, 600.0),    # mOhm
    "ir_growth_pct":            (-5.0, 100.0),    # %
    "cv_phase_fraction":        (0.0, 0.6),       # fraction
    "voltage_slope":            (-5.0e-3, 5.0e-3),# V/cycle
    "voltage_variance":         (0.0, 0.1),       # V^2
    "charge_efficiency":        (0.80, 1.0),      # ratio
    "discharge_efficiency":     (0.78, 1.0),      # ratio
}
assert set(FEATURE_RANGES) == set(FEATURE_KEYS), "FEATURE_RANGES must cover all 14 canonical features"
