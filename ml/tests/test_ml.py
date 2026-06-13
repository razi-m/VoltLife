"""
Validation suite for the VoltLife ML subsystem (Phase 13).

Covers the master plan completion criteria:
  - output contract (keys, types, ranges) verified against spec
  - RUL clamps enforced (edge cases)
  - Grade D hard safety override + blocks deployment
  - model_v1.pkl bundle loads with all required keys
  - missing-feature handling never crashes
  - low confidence routes to inspection
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np
import joblib
import pytest

import shared_constants as C
import predict as P
from grade import assign_grade, safety_triggered

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(HERE, "models", "model_v1.pkl")


def _healthy():
    b = P.load_bundle()
    mean = np.array(b["ood_envelope"]["mean"])
    f = {k: float(mean[i]) for i, k in enumerate(C.FEATURE_KEYS)}
    f["rated_capacity_kwh"] = 40.0
    return f


# ---- bundle ----
def test_bundle_loads_with_required_keys():
    b = joblib.load(MODEL)
    for k in ["soh_model", "rul_q10", "rul_q50", "rul_q90", "feature_keys",
              "metrics", "ood_envelope", "shap_background", "version", "trained_on"]:
        assert k in b, f"bundle missing {k}"
    assert b["feature_keys"] == C.FEATURE_KEYS
    assert len(C.FEATURE_KEYS) == 14


def test_metrics_thresholds_pass():
    m = json.load(open(os.path.join(HERE, "models", "metrics_v1.json")))
    assert m["soh"]["mae"] < 5.0
    assert m["soh"]["r2"] > 0.85
    assert m["rul"]["coverage"] > 0.80


# ---- output contract ----
def test_output_contract_shape():
    r = P.predict(_healthy())
    for k in ["soh_pct", "rul_years", "rul_cycles", "rul_low", "rul_high",
              "confidence", "grade", "recommendation", "reasons", "explanation"]:
        assert k in r, f"missing contract key {k}"
    assert isinstance(r["soh_pct"], float)
    assert isinstance(r["rul_cycles"], int)
    assert r["confidence"] in ("high", "medium", "low")
    assert r["grade"] in ("S", "A", "B", "C", "D")
    assert isinstance(r["reasons"], list) and len(r["reasons"]) == 3
    rec = r["recommendation"]
    for k in ["top_3", "selected", "score", "reasoning"]:
        assert k in rec
    # explanation entries match the backend AssessmentResult shape
    for e in r["explanation"]:
        assert set(["feature", "value", "impact", "shap", "label"]).issubset(e.keys())
        assert e["impact"] in ("+", "-")


def test_ranges_valid():
    r = P.predict(_healthy())
    assert 0.0 <= r["soh_pct"] <= 100.0
    assert 0 <= r["rul_cycles"] <= C.RUL_CYCLES_MAX
    assert 0.0 <= r["rul_years"] <= C.RUL_YEARS_MAX
    assert 0.0 <= r["rul_low"] <= r["rul_years"] <= r["rul_high"] <= C.RUL_YEARS_MAX


# ---- RUL clamps (edge cases) ----
def test_rul_clamps_extreme_inputs():
    for f in [
        {k: 0.0 for k in C.FEATURE_KEYS},
        {k: 1e6 for k in C.FEATURE_KEYS},
        {k: -1e6 for k in C.FEATURE_KEYS},
    ]:
        r = P.predict(dict(f))
        assert 0 <= r["rul_cycles"] <= C.RUL_CYCLES_MAX
        assert 0.0 <= r["rul_years"] <= C.RUL_YEARS_MAX
        assert 0.0 <= r["rul_low"] <= r["rul_high"] <= C.RUL_YEARS_MAX
        assert not (np.isnan(r["soh_pct"]) or np.isinf(r["soh_pct"]))


# ---- Grade D hard safety override ----
def test_grade_d_on_overheat():
    g, blocked, route, note = assign_grade(95.0, "high", 5.0, 6.0, max_temp_c=60.0, ir_growth_pct=10.0)
    assert g == "D" and blocked and route == "Certified Recycler"


def test_grade_d_on_ir_growth():
    g, blocked, route, note = assign_grade(95.0, "high", 5.0, 6.0, max_temp_c=40.0, ir_growth_pct=70.0)
    assert g == "D" and blocked


def test_grade_d_on_low_soh():
    g, blocked, route, note = assign_grade(55.0, "high", 5.0, 6.0, max_temp_c=40.0, ir_growth_pct=10.0)
    assert g == "D" and blocked


def test_grade_d_cannot_be_overridden_by_high_soh():
    # high SoH but unsafe temperature -> still D
    trig, why = safety_triggered(99.0, 56.0, 5.0)
    assert trig


def test_grade_d_blocks_deployment_via_predict():
    f = _healthy()
    f["max_temp_c"] = 61.0  # safety trigger
    r = P.predict(f)
    assert r["grade"] == "D"
    assert r["recommendation"]["selected"] == "Certified Recycler"
    # FIX 4: Grade D top_3 padded to exactly 3, recycler first
    assert len(r["recommendation"]["top_3"]) == 3
    assert r["recommendation"]["top_3"][0] == "Certified Recycler"


# ---- missing features ----
def test_missing_features_no_crash():
    f = {"cycle_count": 400, "capacity_fade_pct": 15.0}  # 12 missing
    r = P.predict(f)
    assert r["grade"] in ("S", "A", "B", "C", "D")
    assert r["confidence"] in ("high", "medium", "low")
    assert len(r["reasons"]) == 3


def test_low_confidence_routes_to_inspection():
    # many missing features -> low confidence -> inspection (not auto-deploy)
    f = {"capacity_fade_pct": 12.0}  # 13 missing -> low
    r = P.predict(f)
    assert r["confidence"] == "low"
    # not grade D, so the low-confidence inspection route applies
    if r["grade"] != "D":
        assert r["recommendation"]["selected"] == "Inspection Required"


def test_never_raises_on_garbage():
    r = P.predict({"cycle_count": "not_a_number", "capacity_fade_pct": None})
    assert r["grade"] in ("S", "A", "B", "C", "D")


# ---- fleet ----
def test_fleet_generated_and_distributed():
    fp = os.path.join(HERE, "data", "fleet.json")
    if not os.path.exists(fp):
        pytest.skip("fleet not generated")
    blob = json.load(open(fp))
    assert blob["count"] == 847
    dist = blob["grade_distribution"]
    assert set(dist.keys()) == {"S", "A", "B", "C", "D"}
    assert all(dist[g] > 0 for g in ["S", "A", "B", "C", "D"]), "every grade must be populated"
    # every battery has a complete assessment
    for bat in blob["batteries"][:50]:
        assert "assessment" in bat and bat["assessment"]["grade"] in ("S", "A", "B", "C", "D")
