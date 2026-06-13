# Claude Code — VoltLife ML Fix Prompt

Paste everything below the line into Claude Code:

---

```
Read ML_VALIDATION_REPORT.md at the root of this project.
Score is 117/130. Four fixes required before Phase 3.

─────────────────────────────────────────
FIX 1 — recommend.py (HIGH)
─────────────────────────────────────────
The scoring logic is inverted.
A Grade S battery with SoH 95% ranks EV Charging Buffer
LAST (0.565) because headroom-over-minimum scoring gives
near-zero scores to premium destinations (min_soh 90)
and high scores to low-tier destinations (min_soh 60).

Fix the scoring logic to reward tier-match:
- Premium batteries (S/A) must surface premium
  destinations (EV Charging Buffer, Solar Storage)
  in the top 3.
- Do NOT use headroom-over-minimum scoring.
- After fixing, run all 5 recommendation test cases.
- Confirm Grade S + SoH 95% → EV Charging Buffer
  appears in top_3.

─────────────────────────────────────────
FIX 2 — explain.py (MEDIUM)
─────────────────────────────────────────
Reason strings currently embed numeric values, e.g.:
  "High capacity fade (15.5%) — significant ageing"
  "High discharge efficiency (0.953)"

The spec requires NO numeric values in reason strings.

Remove all {v:.1f} and any numeric formatting from
every template in explain.py lines 24–66.

Correct form:
  "High capacity fade detected — significant ageing"
  "High discharge efficiency — strong charge retention"

Same input must still return the same output.
Run the determinism test after fixing.

─────────────────────────────────────────
FIX 3 — predict.py + shared_constants.py (MEDIUM)
─────────────────────────────────────────
The frozen output contract and the backend schema
conflict. The backend's AssessmentResult already
requires explanation. Decision: expand the contract.

The canonical frozen output contract now officially
includes explanation and volt_ai. It is:

  soh_pct        → float
  rul_years      → float
  rul_cycles     → int
  rul_low        → float
  rul_high       → float
  confidence     → "high" | "medium" | "low"
  grade          → "S" | "A" | "B" | "C" | "D"
  recommendation → object
  reasons        → list
  explanation    → object
  volt_ai        → object

Update shared_constants.py to document this as the
canonical contract.
Confirm predict.py returns all 11 fields correctly.
Run output contract test cases.

─────────────────────────────────────────
FIX 4 — recommend.py (LOW)
─────────────────────────────────────────
Grade D currently returns only 1 item in top_3.
The spec requires top_3 to always contain exactly
3 items.

For Grade D, pad top_3 as follows:
  [
    "Certified Recycler",
    "Inspection Required",
    "Awaiting Disposal"
  ]

─────────────────────────────────────────
AFTER ALL FIXES
─────────────────────────────────────────
Run the full test suite: ml/tests/test_ml.py
All 14 tests must pass.
Report results for each test by name.
Do NOT touch any files outside the ml/ folder.
Do NOT modify any backend or frontend files.
```
