# 11 — Pitch Structure & Judge Q&A (Owner: Zaid · everyone drills)

## Pitch skeleton (~5 min slot: 1 min setup, 3 min demo, 1 min close — flex to the real slot at kickoff)

1. **Problem (3 sentences):** 128 GWh retiring by 2030 (NITI Aayog) · 70–80% capacity left · no system decides each battery's fate — so value is scrapped early and waste is mismanaged.
2. **Demo** — doc 09. The demo IS the pitch.
3. **What's real (1 slide):** ML trained on NASA/CALCE · leave-one-cell-out MAE = [Razi's number] · SHAP explanations · real optimizer · BPAN-style passports · cited impact math. Fleet + demand registry simulated — and labeled.
4. **Why now (1 slide):** BWMR 2022 EPR targets ramping to 90% recovery · MoRTH Battery Aadhaar draft, rollout 2027 · ₹8,300 cr/yr second-life market (WRI). "The identity layer is mandated. We built the intelligence layer."
5. **Close:** impact page live + "Every battery deserves a second life — and now there's a system that decides it."

Slides: ≤ 6, dark theme matching the dashboard, numbers in mono. The deck is garnish; never present slides while the cascade could be running instead.

## Q&A bank — drill at H24 and H32 (Zaid grills, domain owner answers, 20s max each)

**ML / Data (Razi)**

1. *"Where's the training data from?"* — NASA PCoE + CALCE — the standard public Li-ion degradation benchmarks: full cycle histories to end-of-life with capacity, temperature, and impedance.
2. *"Cell-level data, but you claim EV packs?"* — Correct, and deliberate: public pack-level telemetry barely exists. Our features — fade rate, knee detection, IR growth, thermal stress — are degradation signals that exist at pack level in any BMS log. The pipeline ingests pack telemetry unchanged; the model retrains in minutes when an OEM connects.
3. *"Accuracy?"* — [X]% SoH MAE under **leave-one-cell-out** cross-validation — no cycles from a test cell ever seen in training. RUL always ships with a quantile interval; we'd rather be honest than precise.
4. *"Why no deep learning?"* — ~30 cells. Gradient boosting beats an LSTM at this scale, trains in seconds, and gives SHAP explanations. We chose the method that's right, not the one that's fashionable.
5. *"How do you handle model uncertainty?"* — Quantile spread → confidence tier, plus an out-of-distribution envelope check that forces "low confidence" on inputs unlike training data. Low confidence routes to manual inspection — the model knows what it doesn't know.

**Differentiation (Zaid)**

6. *"Lohum / Attero / BatX already do this?"* — They're vertically integrated processors — they buy, repurpose, recycle in-house. We're the neutral decision layer above: OEMs run VoltLife to grade and route; recyclers like Lohum are *demand-side nodes in our registry*. Watch — grade-D packs route to a recycler in the demo. They're customers, not competitors.
7. *"Tata Elxsi already built Battery Aadhaar."* — Tata Elxsi's platform and MoRTH's BPAN draft are the **identity layer** — the record. Nobody has shipped the **intelligence layer** — the engine that computes BPAN's dynamic fields (SoH, status) and decides deployment. Passports record history; VoltLife writes the next chapter. And our IDs follow the draft's format.
8. *"Why won't an OEM build this internally?"* — Same reason they didn't build UPI: routing needs a *network* — many OEMs' supply meeting many buyers' demand plus recyclers. A neutral layer aggregates; in-house tools fragment.

**Business (Zaid)**

9. *"Who pays?"* — Three lanes: per-pack assessment fee from OEMs/fleets (a graded pack with a passport sells above scrap — we take a slice of the uplift); EPR-compliance SaaS (BWMR reporting is mandatory and painful); certification fees from second-life buyers who need warrantied supply.
10. *"Where does real telemetry come from?"* — Every EV BMS already logs it; today it dies in silos. Two forcing functions: EPR liability (BWMR) and BPAN's dynamic-data requirement by 2027. Compliance is the wedge; intelligence is the lock-in.
11. *"Go-to-market?"* — Start with 2W/3W fleet operators — they retire packs in batches, feel EPR pressure first, and have the simplest packs. Then OEMs, then the registry network effect.

**Technical (Farhan)**

12. *"What's actually autonomous?"* — The full loop: ingest → assess → match → route → record, no human in the loop until dispatch approval. Hard safety gates (grade D cannot deploy), every decision logged with reasons.
13. *"Scale beyond 847?"* — Inference is sub-ms per pack; the pipeline is stateless and embarrassingly parallel; Postgres partitions by month. 847 in the demo is paced *slower* for visibility — the math is the easy part.
14. *"What if the AI misgrades a dangerous battery?"* — Safety isn't ML's job. Hard rules — SoH floor, IR growth ceiling, thermal-event flags — sit *above* the model and cannot be overridden. Plus conservative grading at low confidence, human dispatch approval, full audit trail.
15. *"Why not blockchain for the passport?"* (ETHIndia sponsor in the room) — MoRTH's draft is server-based with tiered access, so we match the spec. Passport event hashes could anchor on-chain for tamper-evidence later — it's a feature flag away, but consensus isn't the bottleneck; intelligence is.

**Impact (anyone)**

16. *"How is carbon savings computed?"* — Usable kWh × 60 kg CO₂e/kWh of avoided new-battery manufacturing — deliberately below the published 48–120 range median. Formula and citations are in the repo; happy to walk through one battery's math live.
17. *"Is the 847-battery batch real?"* — Simulated batch, real physics: degradation trajectories fitted from NASA/CALCE cells, perturbed, mapped to Indian fleet metadata. OEMs don't hand telemetry to hackathon teams — yet. Everything downstream of the CSV is real computation.
18. *"What's the single biggest weakness?"* — Data access: the model is only as good as the telemetry OEMs share. That's why we lead with the compliance wedge — EPR and BPAN make sharing mandatory anyway. We'd rather name our hardest problem than have you find it.

**Curveballs**

19. *"Couldn't ChatGPT do this?"* — An LLM can't predict capacity fade from voltage curves or optimize an assignment under constraints. There is no LLM in our decision loop — gradient boosting, quantile regression, SHAP, and an optimizer. The explanations are templated from model internals, deterministic and auditable.
20. *"What did you NOT build, and why?"* — Marketplace, blockchain, route planning, demand forecasting. One unforgettable working loop beats ten half-features. Everything we showed ran live.

## Delivery rules

Domain owner answers; one voice per question; 20 seconds then stop talking. "Great question — [answer]" once, max. If nobody knows: "We didn't get to that in 36 hours; here's how we'd approach it —" honesty outscores bluffing every time.
