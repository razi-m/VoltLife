import os

# Physical & Sustainability constants
CYCLES_PER_YEAR = 300
DEPTH_OF_DISCHARGE = 0.80
ROUND_TRIP_EFFICIENCY = 0.90
CARBON_AVOIDED_MFR_KG_PER_KWH = 60.0  # avoided new-battery manufacturing

# Grading policy thresholds
SAFETY_MAX_TEMP = 55.0
SAFETY_IR_GROWTH = 60.0
SAFETY_MIN_SOH = 60.0

GRADE_S_MIN_SOH = 90.0
GRADE_S_MAX_IR_GROWTH = 20.0
GRADE_S_MAX_THERMAL_STRESS = 20.0  # T_LOW
GRADE_S_MIN_RUL_YEARS = 4.0

GRADE_A_MIN_SOH = 80.0
GRADE_B_MIN_SOH = 70.0
GRADE_C_MIN_SOH = 60.0

# Site matching weights (Stage 2 scoring)
WEIGHT_CAPACITY_MATCH = 0.30
WEIGHT_GRADE_HEADROOM = 0.25
WEIGHT_PROXIMITY = 0.20
WEIGHT_CARBON_BENEFIT = 0.15
WEIGHT_SITE_PRIORITY = 0.10

# Bounding box coordinates for India (6-37 N, 68-98 E)
INDIA_BOUNDS = {
    "min_lat": 6.0,
    "max_lat": 37.0,
    "min_lng": 68.0,
    "max_lng": 98.0
}

# Ingestion configuration
MAX_INGESTION_ROWS = 5000

# Pacing configuration (can be overridden via environment variable)
DEFAULT_PACE_S = 0.15
