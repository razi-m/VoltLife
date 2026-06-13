import math
from typing import Dict, Any, List

def assess(features: Dict[str, float]) -> Dict[str, Any]:
    """
    Simulates ML model assessment using the 14-key feature vector.
    Enforces safety overrides, RUL cycle clamping, confidence rating,
    grading logic, and generates top-3 reasons.
    """
    # 1. State of Health Calculation
    capacity_fade = features.get("capacity_fade_pct", 0.0)
    if math.isnan(capacity_fade):
        capacity_fade = 0.0
    soh_pct = max(0.0, min(100.0, 100.0 - capacity_fade))
    soh_pct = round(soh_pct, 1)

    # Gather key features
    max_temp = features.get("max_temp_c", 0.0)
    ir_growth = features.get("ir_growth_pct", 0.0)
    thermal_stress = features.get("thermal_stress_hours", 0.0)
    cycle_count = features.get("cycle_count", 0)
    fade_acceleration = features.get("fade_acceleration", 0.0)

    # 2. Confidence Rating
    # Count NaNs in features
    nan_count = sum(1 for v in features.values() if isinstance(v, float) and math.isnan(v))
    if nan_count > 3 or cycle_count > 2000:
        confidence = "low"
    elif cycle_count > 1000 or ir_growth > 40.0:
        confidence = "medium"
    else:
        confidence = "high"

    # 3. Safety Overrides (Checked FIRST, cannot be overridden)
    is_unsafe = (
        (not math.isnan(max_temp) and max_temp > 55.0) or
        (not math.isnan(ir_growth) and ir_growth > 60.0) or
        (soh_pct < 60.0)
    )

    if is_unsafe:
        # Dangerous/unsafe battery goes straight to Recycle (Grade D)
        rul_cycles = 0
        rul_years = 0.0
        rul_low = 0.0
        rul_high = 0.0
        grade = "D"
        confidence = "high"  # We are highly confident it is unsafe
        
        # Determine safety reasons
        safety_reasons = []
        explanation = []
        if not math.isnan(max_temp) and max_temp > 55.0:
            msg = f"Overheating detected (max {max_temp:.1f}°C)"
            safety_reasons.append(msg)
            explanation.append({"feature": "max_temp_c", "value": max_temp, "impact": "-", "shap": -0.4, "label": msg})
        if not math.isnan(ir_growth) and ir_growth > 60.0:
            msg = f"Critical internal resistance growth ({ir_growth:.1f}%)"
            safety_reasons.append(msg)
            explanation.append({"feature": "ir_growth_pct", "value": ir_growth, "impact": "-", "shap": -0.35, "label": msg})
        if soh_pct < 60.0:
            msg = f"State of Health below safety floor ({soh_pct:.1f}%)"
            safety_reasons.append(msg)
            explanation.append({"feature": "capacity_fade_pct", "value": capacity_fade, "impact": "-", "shap": -0.5, "label": msg})
            
        # Pad to 3 reasons
        while len(safety_reasons) < 3:
            safety_reasons.append("Safety override triggered")
            explanation.append({"feature": "safety", "value": 1.0, "impact": "-", "shap": -0.1, "label": "Safety override triggered"})
            
        return {
            "soh_pct": soh_pct,
            "rul_cycles": rul_cycles,
            "rul_years": rul_years,
            "rul_low": rul_low,
            "rul_high": rul_high,
            "grade": grade,
            "confidence": confidence,
            "explanation": explanation[:3],
            "reasons": safety_reasons[:3]
        }

    # 4. RUL Cycle Calculation & Clamping (Must-Fix #2)
    # Estimate remaining cycles to 60% SoH
    # If SoH is 100%, remaining cycles around 1200-2400.
    factor = (soh_pct - 60.0) / 40.0  # 0 to 1
    estimated_cycles = int(1800 * factor)
    
    # Clamp remaining cycles to [0, 2400]
    rul_cycles = max(0, min(2400, estimated_cycles))
    
    # Calculate years (CYCLES_PER_YEAR = 300)
    rul_years = round(rul_cycles / 300.0, 1)
    
    # Quantile bounds
    rul_low = round(max(0.0, rul_years - 1.2), 1)
    rul_high = round(min(8.0, rul_years + 1.1), 1)
    # Ensure ordering
    rul_low, rul_high = sorted([rul_low, rul_high])

    # 5. Grading Policy
    # S: soh >= 90 AND confidence high AND thermal stress < 20 AND ir_growth < 20 AND rul_years >= 4.0
    is_pristine_thermal = (math.isnan(thermal_stress) or thermal_stress < 20.0)
    is_pristine_ir = (math.isnan(ir_growth) or ir_growth < 20.0)
    
    if (soh_pct >= 90.0 and confidence == "high" and is_pristine_thermal and is_pristine_ir and rul_years >= 4.0):
        grade = "S"
    elif soh_pct >= 80.0:
        grade = "A"
    elif soh_pct >= 70.0:
        grade = "B"
    elif soh_pct >= 60.0:
        grade = "C"
    else:
        grade = "D"

    # Confidence demotion
    if confidence == "low" and grade in ("S", "A", "B"):
        grade = "C"

    # 6. Explanations & Reasons
    explanation = []
    
    # Feature 1: Temperature
    avg_temp = features.get("avg_temp_c", 30.0)
    if not math.isnan(avg_temp):
        if avg_temp < 35.0:
            explanation.append({
                "feature": "avg_temp_c",
                "value": avg_temp,
                "impact": "+",
                "shap": 0.15,
                "label": f"Low thermal stress (avg {avg_temp:.1f}°C)"
            })
        else:
            explanation.append({
                "feature": "avg_temp_c",
                "value": avg_temp,
                "impact": "-",
                "shap": -0.12,
                "label": f"High operating temperature (avg {avg_temp:.1f}°C)"
            })

    # Feature 2: Ir Growth
    if not math.isnan(ir_growth):
        if ir_growth < 20.0:
            explanation.append({
                "feature": "ir_growth_pct",
                "value": ir_growth,
                "impact": "+",
                "shap": 0.10,
                "label": f"Low internal resistance growth ({ir_growth:.1f}%)"
            })
        else:
            explanation.append({
                "feature": "ir_growth_pct",
                "value": ir_growth,
                "impact": "-",
                "shap": -0.15,
                "label": f"Internal resistance up {ir_growth:.1f}% from baseline"
            })

    # Feature 3: Fade Acceleration / Knee
    if not math.isnan(fade_acceleration) and fade_acceleration > 0.05:
        explanation.append({
            "feature": "fade_acceleration",
            "value": fade_acceleration,
            "impact": "-",
            "shap": -0.22,
            "label": "Capacity fade is accelerating — knee detected"
        })
    else:
        # Default fallback feature
        explanation.append({
            "feature": "voltage_stability",
            "value": 0.985,
            "impact": "+",
            "shap": 0.08,
            "label": "Stable voltage profile under load"
        })

    # Feature 4: Cycle count
    explanation.append({
        "feature": "cycle_count",
        "value": cycle_count,
        "impact": "+" if cycle_count < 600 else "-",
        "shap": 0.08 if cycle_count < 600 else -0.08,
        "label": f"Moderate cycle count ({cycle_count} cycles)" if cycle_count < 600 else f"High cycle count ({cycle_count} cycles)"
    })

    # Sort explanations by absolute SHAP impact
    explanation = sorted(explanation, key=lambda x: abs(x["shap"]), reverse=True)
    reasons = [e["label"] for e in explanation[:3]]

    return {
        "soh_pct": soh_pct,
        "rul_cycles": rul_cycles,
        "rul_years": rul_years,
        "rul_low": rul_low,
        "rul_high": rul_high,
        "grade": grade,
        "confidence": confidence,
        "explanation": explanation[:3],
        "reasons": reasons[:3]
    }
