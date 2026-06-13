# 08 — Confidence Engine

## Pushback first (read before implementing)

The instruction "allowed outputs: High, Medium — avoid exposing low confidence during demos" must NOT be implemented as suppression. Two reasons: (1) the wire contract (docs/04) and judge_attacks #5/#7 already commit us to *"the model knows what it doesn't know — low confidence routes to inspection"* — judges have been promised three tiers and a queue; deleting "low" mid-week contradicts our own drilled answers. (2) A model that cannot say "low" is precisely the over-confident black box judges attack.

**Resolution that satisfies the intent:** three tiers exist internally and on the wire; the *demo never shows an ugly low* because we control the demo inputs, and when low fires it renders as a feature ("Under review → inspection queue"), not a wart.

## Signals → tier

```
spread_ratio = (rul_high − rul_low) / max(rul_years, 0.5)
ood_count    = # features outside the training envelope (per-feature [min−10%, max+10%], NaNs count as 0.5)
divergence   = SoH-vs-fade check from 06_soh_model_design.md

tier = "high"    if spread_ratio < 0.5  and ood_count == 0 and not divergence
       "medium"  if spread_ratio < 0.9  and ood_count <= 2 and not divergence
       "low"     otherwise
```

Thresholds in `shared/constants.py`. The envelope (per-feature min/max from training data) ships inside the model bundle (12_*) — confidence is computable offline with zero extra artifacts.

## Demo policy (the actual answer to "avoid exposing low")

1. **Control inputs, not outputs:** the synthetic fleet generator samples from real degradation archetypes → in-distribution by construction. QA harness (14_*) asserts **low ≤ 2% of the 847**; if exceeded, fix the generator jitter, never the confidence code.
2. **Low renders as governance:** UI shows "Under review" chip + inspection-queue routing (innovation #12); a low-confidence battery never auto-deploys (deployment gate). On stage this is a 5-second *strength* beat if it appears at all.
3. **Hard rule:** never remap low→medium in code. If a judge uploads adversarial CSV rows during Q&A (they sometimes do), the system saying "low confidence, manual inspection" is the best possible outcome.

## Consumers

`grade.py`: S-grade requires high; low forces grade ≤ C and blocks deployment. `recommend.py`: low → no site recommendations, status "inspection". UI: chip on DecisionCard/HealthPanel. WS payload: `confidence` field, unchanged (docs/04).
