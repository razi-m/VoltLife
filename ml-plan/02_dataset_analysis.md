# 02 — Dataset Analysis

## NASA PCoE Battery Dataset (primary)

18650 Li-ion cells (2.0 Ah rated), cycled charge/discharge/impedance to failure. Start set: **B0005, B0006, B0007, B0018** (≈24°C ambient, 2A CC discharge, distinct voltage cutoffs 2.7/2.5/2.2/2.5 V). Expansion sets at other ambients (~4°C, ~43°C groups) supply the thermal variation that teaches `avg_temp_c`/`thermal_stress_hours`.

**Available fields** (`.mat` nested structs, per cycle):

- Charge cycles: `voltage_measured`, `current_measured`, `temperature_measured`, `current_charge`, `voltage_charge`, `time` — yields CC/CV phase split → `cv_phase_fraction`, `charge_efficiency`
- Discharge cycles: same series + **`capacity`** (the SoH label source) → `voltage_slope`, `voltage_variance`, `discharge_efficiency`
- Impedance cycles: `Re` (electrolyte), `Rct` (charge transfer) → `internal_resistance_mohm`, `ir_growth_pct`

**Data quality concerns**

| Issue | Impact | Handling |
|---|---|---|
| Capacity regeneration (self-recovery jumps after rest) | Noisy SoH labels, fake "healing" | Median-smooth capacity series (window 5) before labeling; keep raw for features |
| Impedance cycles interleaved, not 1:1 with discharge cycles | IR missing at most cycle indices | Forward-fill IR to nearest discharge cycle; gaps stay NaN (model handles) |
| B0018 irregular/short record | Weak as a held-out cell | Use in train; prefer B0005/06/07 as LOCO test cells for reported metrics |
| Some files have truncated/corrupt cycles | Parser crashes | Skip cycles failing length/monotonicity checks; log counts |
| EOL convention = 70% (1.4 Ah) | Cells stop near 70% — no data below | Extrapolate fitted fade curve to 60% for second-life RUL labels (07_rul_model_design.md) — declared, not hidden |

## CALCE CS2 Dataset (secondary — chemistry/form-factor diversity)

LiCoO₂ prismatic cells, 1.1 Ah, cycled at 0.5C/1C. Distributed as per-date Excel/CSV files per cell (CS2_35, CS2_36, CS2_37, CS2_38 commonly used).

**Available fields:** Cycle_Index, Test_Time, Current, Voltage, Charge_Capacity, Discharge_Capacity, sporadic Internal_Resistance. **Concerns:** files must be concatenated in date order (filename parsing); occasional column drift between export batches; IR coverage sparse; temperature column often absent (→ temp features NaN for CALCE rows — fine, model is NaN-native, and this *tests* missing-field robustness). 

**Role:** second source proving features aren't NASA-overfit. If parsing burns >2 of tonight's hours → cut (doc 10 cut-line 5) and adjust judge answer Q2 accordingly.

## Feature candidates → confirmed in 03_feature_spec.md

All 14 canonical features are computable from the fields above; `thermal_stress_hours` and `max_temp_c` are NASA-only until CALCE temp data exists — acceptable.

## Dataset limitations (own these — they're in judge_attacks A/B)

Cell-level not pack-level (#3); N≈4–8 cells per condition (#2); lab protocols not road duty (#12); no LFP chemistry (#11); nothing below 60% SoH. Every limitation has a scripted answer — the model card in the repo README states them proactively.
