"""
recommend.py — Deployment Recommendation Engine  (Phase 8)

NOT an ML model — a transparent, deterministic scoring engine.

Output (frozen contract):
  {"top_3": [names], "selected": name, "score": float, "reasoning": str}

Scoring is TIER-ALIGNMENT (validation 2.0, ISSUE #1). The score rewards:
  1. Tier alignment      — destination requirement matched to battery grade
                           (peaks when the destination's min_grade == battery grade,
                            then decays as the gap widens). A premium battery is NOT
                            steered to a low-tier site.
  2. Use-case suitability — higher-demand destinations are the premium use cases;
                            a capable battery is matched to substantial workloads.
  3. Battery quality      — SoH + remaining-life headroom.

The OLD headroom-over-minimum / capacity-over-demand term is REMOVED: it rewarded
"excess headroom", so a 95% pack scored a low-tier Street Lighting site (min_soh 60)
higher than the premium EV Charging Buffer (min_soh 90). Ranking is now capacity-
independent (capacity is reported in the reasoning, not used to invert the ranking).

Resulting premium ladders (capability descending):
  S -> EV Charging Buffer, Industrial Backup, Solar Storage
  A -> Industrial Backup, Solar Storage, Telecom Tower
  B -> Solar Storage, Rural Microgrid, Street Lighting
  C -> Street Lighting (+ aspirational next-step sites)
  D -> Certified Recycler (deployment blocked)

Hard rules:
  - grade "D"        -> Certified Recycler (deployment blocked); top_3 padded to 3
  - low confidence   -> route to inspection (NOT auto-deployed)
top_3 always contains exactly 3 items.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shared_constants as C

# Largest destination demand in the catalog — normaliser for use-case suitability.
_MAX_DEMAND_KWH = max((d["demand_kwh"] for d in C.DESTINATIONS), default=1.0) or 1.0

# Scoring weights (sum 1.0). Tier alignment dominates so premium destinations
# surface for premium batteries; demand breaks within-tier ties (higher demand
# first); quality is a mild healthy-pack reward.
_W_TIER, _W_DEMAND, _W_QUALITY = 0.62, 0.26, 0.12


def _dest_tier(dest):
    """Premium-ness of a destination in [0,1]: higher min_grade/min_soh -> higher.
    Used only for aspirational padding ordering, not for primary scoring."""
    return 0.6 * (C.GRADE_RANK[dest["min_grade"]] / 5.0) + 0.4 * (dest["min_soh"] / 100.0)


def _tier_alignment(grade, dest):
    """1.0 when the destination's required grade == battery grade; decays linearly
    with the grade gap (range of GRADE_RANK is 4, so divide by 4)."""
    gap = abs(C.GRADE_RANK[grade] - C.GRADE_RANK[dest["min_grade"]])
    return max(0.0, 1.0 - gap / 4.0)


def _eligible(dest, grade, soh_pct):
    if dest["name"] == "Certified Recycler":
        return grade == "D"
    return C.GRADE_RANK[grade] >= C.GRADE_RANK[dest["min_grade"]] and soh_pct >= dest["min_soh"]


def _score(dest, soh_pct, rul_years, grade, capacity_kwh=None):
    """Tier-alignment score in [0,1]. capacity_kwh is accepted but intentionally
    NOT used in ranking (it previously inverted the intent)."""
    tier_align = _tier_alignment(grade, dest)
    demand_fit = min(1.0, dest["demand_kwh"] / _MAX_DEMAND_KWH)
    quality = 0.5 * min(1.0, max(0.0, soh_pct) / 100.0) + \
              0.5 * min(1.0, max(0.0, rul_years) / C.RUL_YEARS_MAX)
    return _W_TIER * tier_align + _W_DEMAND * demand_fit + _W_QUALITY * quality


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
