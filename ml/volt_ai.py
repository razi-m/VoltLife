"""
volt_ai.py — Volt AI Layer  (Phase 10)

Explanation layer ONLY — NOT a prediction layer. Volt AI NEVER modifies
soh_pct, rul_cycles, rul_years, confidence, grade or recommendation score.
Deterministic, template-based, NO LLM calls. Same input -> same output.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_GRADE_WORD = {"S": "pristine", "A": "excellent", "B": "good", "C": "fair", "D": "end-of-life"}


def generate_narratives(result, battery_meta=None):
    meta = battery_meta or {}
    ref = meta.get("external_ref") or meta.get("battery_id") or "this battery"
    soh = result["soh_pct"]; grade = result["grade"]; conf = result["confidence"]
    rul_y = result["rul_years"]; rul_lo = result["rul_low"]; rul_hi = result["rul_high"]
    reasons = result.get("reasons", [])
    rec = result.get("recommendation", {})
    selected = rec.get("selected", "inspection")
    grade_word = _GRADE_WORD.get(grade, "assessed")

    executive_summary = (
        f"{ref} is in {grade_word} condition (Grade {grade}, SoH {soh:.1f}%) with an "
        f"estimated {rul_y:.1f} years of remaining useful life ({rul_lo:.1f}-{rul_hi:.1f} yr range, "
        f"{conf} confidence). Recommended next step: {selected}.")

    assessment_narrative = (
        f"State-of-health is {soh:.1f}% of nominal capacity, placing the pack in Grade {grade}. "
        f"Remaining useful life is projected at {rul_y:.1f} years (model confidence: {conf}). "
        f"Key drivers: " + "; ".join(reasons[:3]) + ".")

    if grade == "D":
        deployment_justification = (
            f"Deployment is blocked. A hard safety override classifies {ref} as Grade D, so it is "
            f"routed directly to a Certified Recycler. {rec.get('reasoning', '')}")
    elif conf == "low":
        deployment_justification = (
            f"{ref} is held for manual inspection because model confidence is low. "
            f"No automatic deployment is permitted until a reviewer confirms the assessment.")
    else:
        deployment_justification = (
            f"{ref} is matched to {selected} (score {rec.get('score', 0)}/100). "
            f"{rec.get('reasoning', '')}")

    impact_narrative = (
        f"Reusing {ref} in a second-life application avoids premature recycling and unlocks roughly "
        f"{rul_y:.1f} more years of usable energy storage, displacing new-cell manufacturing and "
        f"the associated carbon footprint." if grade != "D" else
        f"{ref} has reached end-of-life; responsible recycling recovers critical materials "
        f"(lithium, cobalt, nickel) and keeps them out of landfill.")

    human_readable_report = "\n".join([
        f"VOLTLIFE ASSESSMENT — {ref}",
        f"Grade: {grade} ({grade_word})   SoH: {soh:.1f}%   RUL: {rul_y:.1f} yr [{rul_lo:.1f}-{rul_hi:.1f}]   Confidence: {conf}",
        f"Recommendation: {selected}",
        "Why: " + "; ".join(reasons[:3]),
        deployment_justification,
    ])

    return {
        "executive_summary": executive_summary,
        "assessment_narrative": assessment_narrative,
        "deployment_justification": deployment_justification,
        "impact_narrative": impact_narrative,
        "human_readable_report": human_readable_report,
    }
