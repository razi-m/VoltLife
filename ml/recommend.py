"""
recommend.py — Deployment Recommendation Engine  (Phase 8)

NOT an ML model — a transparent, deterministic scoring engine.

Output (frozen contract):
  {"top_3": [names], "selected": name, "score": float, "reasoning": str}

Scoring is TIER-MATCH (fixed per validation FIX 1): premium destinations
(higher min_grade / min_soh) score HIGHER for capable batteries, so a Grade S
/ high-SoH pack surfaces premium sites (EV Charging Buffer, Solar Storage) in
the top 3. Headroom-over-minimum scoring is intentionally NOT used.

Hard rules:
  - grade "D"        -> Certified Recycler (deployment blocked); top_3 padded to 3
  - low confidence   -> route to inspection (NOT auto-deployed)
top_3 always contains exactly 3 items.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared_constants as C


def _dest_tier(dest):
    """Premium-ness of a destination in [0,1]: higher min_grade/min_soh -> higher."""
    return 0.6 * (C.GRADE_RANK[dest["min_grade"]] / 5.0) + 0.4 * (dest["min_soh"] / 100.0)


def _eligible(dest, grade, soh_pct):
    if dest["name"] == "Certified Recycler":
        return grade == "D"
    return C.GRADE_RANK[grade] >= C.GRADE_RANK[dest["min_grade"]] and soh_pct >= dest["min_soh"]


def _score(dest, soh_pct, rul_years, grade, capacity_kwh):
    """Tier-match score in [0,1]: reward premium destinations + healthy/long-life packs."""
    tier = _dest_tier(dest)                                   # premium destination -> higher
    soh_fit = min(1.0, max(0.0, soh_pct) / 100.0)
    rul_fit = min(1.0, max(0.0, rul_years) / C.RUL_YEARS_MAX)
    cap_fit = 1.0
    if dest["demand_kwh"] > 0 and capacity_kwh:
        cap_fit = min(1.0, float(capacity_kwh) / dest["demand_kwh"])
    return 0.45 * tier + 0.30 * soh_fit + 0.15 * rul_fit + 0.10 * cap_fit


def _rank(grade, soh_pct, rul_years, capacity_kwh):
    scored = []
    for dest in C.DESTINATIONS:
        if dest["name"] == "Certified Recycler":
            continue
        if not _eligible(dest, grade, soh_pct):
            continue
        scored.append((dest["name"], _score(dest, soh_pct, rul_years, grade, capacity_kwh)))
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored


def _pad_top3(names):
    """Guarantee exactly 3 destinations: pad with the closest tier-up sites as
    aspirational 'next-step' options (used by the backend 'why not?' panel)."""
    names = list(names[:3])
    if len(names) < 3:
        extras = [d for d in C.DESTINATIONS
                  if d["name"] != "Certified Recycler" and d["name"] not in names]
        extras.sort(key=_dest_tier)  # ascending -> closest above the battery first
        for d in extras:
            names.append(d["name"])
            if len(names) == 3:
                break
    return names[:3]


def recommend(grade, soh_pct, rul_years, confidence, capacity_kwh=None, location=None, sites=None):
    """Return {top_3 (exactly 3), selected, score, reasoning} (+ score_raw, blocked)."""
    # Grade D — mandatory recycler route, deployment blocked. top_3 padded to 3 (FIX 4).
    if grade == "D":
        return {
            "top_3": ["Certified Recycler", "Inspection Required", "Awaiting Disposal"],
            "selected": "Certified Recycler",
            "score": 100.0,
            "score_raw": 1.0,
            "reasoning": "Grade D safety override — battery is routed directly to a "
                         "Certified Recycler. Deployment is blocked and cannot be overridden.",
            "blocked": True,
        }

    ranked = _rank(grade, soh_pct, rul_years, capacity_kwh)

    # Low confidence — route to inspection rather than auto-deploy
    if confidence == "low":
        top3 = _pad_top3([d for d, _ in ranked])
        return {
            "top_3": top3,
            "selected": "Inspection Required",
            "score": round((ranked[0][1] * 100) if ranked else 0.0, 1),
            "score_raw": round(ranked[0][1] if ranked else 0.0, 4),
            "reasoning": "Low model confidence — battery routed to manual inspection before "
                         "any deployment. Candidate destinations shown for reviewer context.",
            "blocked": False,
        }

    if not ranked:
        return {"top_3": _pad_top3([]), "selected": "Inspection Required",
                "score": 0.0, "score_raw": 0.0,
                "reasoning": "No eligible destination met the grade/SoH thresholds.",
                "blocked": False}

    top3 = _pad_top3([d for d, _ in ranked])
    best_name, best_raw = ranked[0]
    reasoning = (f"Selected {best_name}: Grade {grade}, SoH {soh_pct:.1f}%, "
                 f"~{rul_years:.1f} yr remaining life best match this premium destination's "
                 f"reliability and demand profile (score {round(best_raw*100)}/100).")
    return {
        "top_3": top3,
        "selected": best_name,
        "score": float(round(best_raw * 100, 1)),
        "score_raw": float(round(best_raw, 4)),
        "reasoning": reasoning,
        "blocked": False,
    }
