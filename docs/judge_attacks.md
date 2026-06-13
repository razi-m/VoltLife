# Judge Attacks — 102 Ways to Kill VoltLife (and the Answers)

Role-played as the harshest judge in the room. Format per attack: **Q** (the attack) · **D** (why it's dangerous) · **A** (best answer, ≤20 s spoken) · **C** (our confidence in the answer: High/Med/Low). Drill at H24 and H32 — Zaid asks, domain owner answers. The Medium/Low-confidence ones are where to spend drill time. Cross-references: doc 11 has full scripts for the 20 most likely.

Conf legend: **H** = we win this exchange · **M** = survivable, needs exact wording · **L** = genuine weakness, answer with honesty + roadmap.

---

## A. ML & Modeling (Razi answers)

| # | Q · D · A | C |
|---|---|---|
| 1 | **Q:** SoH is just capacity ÷ rated — why is this AI and not a formula? **D:** Strikes at "AI is necessary"; fumble = ChatGPT-wrapper bucket. **A:** Measuring capacity requires a full controlled discharge — hours per pack, impossible at fleet scale. We *estimate* it from operational signals (partial curves, IR, thermal history) — that's a learning problem. And RUL has no formula at all: it's prediction under uncertainty. | H |
| 2 | **Q:** ~34 cells of training data is laughable. **D:** True at face value. **A:** Sliding-window sampling turns 34 full lifetimes into thousands of state→outcome rows. At this scale boosted trees beat deep nets — that's why we chose them — and we validate leave-one-cell-out so the number we report is honest. | H |
| 3 | **Q:** Trained on 18650 cells, claiming EV packs. **D:** The #1 credibility attack. **A:** Doc 11 Q2 script — features are chemistry-agnostic degradation signals present in any BMS log; pipeline ingests pack telemetry unchanged; retrains in minutes when an OEM connects. | H |
| 4 | **Q:** Did you split train/test randomly? **D:** If yes, leakage — instant kill from an ML judge. **A:** No — leave-one-cell-out exactly because random splits leak cycles from the same cell. Happy to show the CV code. | H |
| 5 | **Q:** What MAE, and is that good? **D:** No number = no model. **A:** [X]% SoH MAE cross-cell (state your trained number). Literature reports 1–3% on the same data with within-cell splits — ours is the harder, honest setting. | H |
| 6 | **Q:** RUL in *years* is fantasy — you don't know future usage. **D:** Correct in general. **A:** We state the duty assumption on-screen: 300 cycles/year, 2W fleet duty. RUL ships as a range, not a point. In production the duty cycle comes from the operator's own profile — one parameter. | H |
| 7 | **Q:** Quantile regression isn't calibrated uncertainty. **D:** Statistically literate attack. **A:** Agreed — we report empirical coverage on held-out cells, plus an out-of-distribution envelope that forces low confidence on unfamiliar inputs. Calibrated conformal intervals are the named next step. | M |
| 8 | **Q:** SHAP on correlated features produces artifacts. **D:** True; could make explanations look decorative. **A:** Known limitation — we template only the stable top features by mean signed contribution, and the explanations are sanity-checked against electrochemical priors (heat ↓ health, knee ↓ RUL). They're audit trails, not causal claims. | M |
| 9 | **Q:** Why not a transformer / battery foundation model? **D:** Fashion test, inverted trap. **A:** 34 cells. The pipeline is model-agnostic — swap the backbone when data justifies it. We optimized for *right*, not *impressive*. | H |
| 10 | **Q:** Your knee detection is a slope difference — crude. **D:** Knee-point literature is sophisticated. **A:** It's one engineered feature, not the predictor; the model weighs it among 12+. Bacon-style knee-point algorithms are a drop-in upgrade — same feature slot. | H |
| 11 | **Q:** LFP has a flat voltage curve — your voltage features die. **D:** Real chemistry gotcha. **A:** Correct — chemistry is itself a feature; for LFP the model leans on capacity fade, IR growth, and thermal history. CALCE adds prismatic cells; LFP-specific data is on the roadmap and the feature set already degrades gracefully. | M |
| 12 | **Q:** NASA cycled cells at fixed lab temperatures — real fleets see chaos. **D:** Distribution-shift attack. **A:** That controlled variation is what isolates thermal aging; we aggregate to robust features (stress-hours, averages) rather than raw traces. Field recalibration is exactly why assessments carry model_version and re-assessment events exist. | M |
| 13 | **Q:** Why 70% as end-of-life? **D:** Sounds arbitrary. **A:** Industry and NASA convention for first-life EOL — and it's a config constant, not gospel. Second-life EOL (60%) is separately configurable. | H |
| 14 | **Q:** How do you handle model drift? **D:** Production-maturity probe. **A:** Every assessment row stores model_version; re-assessment is a first-class lifecycle event; drift monitoring = compare predicted vs measured at next assessment. The schema was built for it. | H |
| 15 | **Q:** A lookup table could match your model. **D:** Dismissiveness. **A:** On four NASA cells, almost. Across chemistries, duty cycles, and temperatures — no. And a lookup table can't output intervals, confidence, or explanations, which is what makes decisions defensible. | H |

## B. Data & Datasets (Razi answers)

| # | Q · D · A | C |
|---|---|---|
| 16 | **Q:** Where is the training data from, exactly? Licensed? **D:** Basic, must be instant. **A:** NASA Prognostics Center of Excellence open repository and CALCE (Univ. of Maryland) — the standard public Li-ion degradation benchmarks, openly licensed for research. | H |
| 17 | **Q:** So the 847-battery demo is fake data. **D:** "Demo theater" accusation. **A:** Doc 11 Q17 — simulated batch, real physics: trajectories fitted from real cells, perturbed, mapped to Indian fleet metadata. Everything downstream of the CSV is real computation. We label it simulated on the slide. | H |
| 18 | **Q:** What if telemetry fields are missing? **D:** Real-world readiness. **A:** HistGradientBoosting handles missing values natively; confidence degrades explicitly; below a minimum field set (cycles + capacity or IR) the battery routes to the inspection queue instead of being guessed at. | H |
| 19 | **Q:** Every OEM logs different formats. **D:** Integration skepticism. **A:** Ingestion normalizes to one schema via a column template — per-OEM adapters are config, not code. And BPAN will standardize exactly these fields by 2027; we're aligned with the draft. | H |
| 20 | **Q:** There's zero public Indian battery data. You built on foreign cells. **D:** India-washing accusation. **A:** True, and it's the gap we exist to close: the EPR + BPAN compliance wedge is what generates India's first structured retirement dataset — inside VoltLife. | M |
| 21 | **Q:** Cheap 2W packs don't have smart BMS. **D:** Market-reality attack. **A:** Even basic BMS logs voltage, current, temperature — enough for our derived features. Worst case: a capacity-test intake lane at collection hubs; our UART rig is a working prototype of exactly that. | M |
| 22 | **Q:** Garbage in, garbage out — sensor noise? **D:** Data-quality probe. **A:** Range and plausibility gates at ingestion (with a reject report — you saw 3 rejects in the demo), plus OOD detection downstream. Bad data gets quarantined, not graded. | H |
| 23 | **Q:** Why not collect your own dataset with that UART rig? **D:** Effort-shaming. **A:** One rig produces one cell's slow story — months per lifetime. The rig proves the intake path; public benchmarks prove the model; fleets provide scale. | H |
| 24 | **Q:** Battery location history = surveillance? **D:** Privacy curveball. **A:** Pack telemetry isn't personal data and we hold city-level location only. BPAN's tiered access (public static / private dynamic) is exactly our model. | H |
| 25 | **Q:** What's your data moat if everyone has NASA data? **D:** Moat probe in data clothing. **A:** The moat isn't NASA — it's the closed loop we accumulate: predicted grade vs actual second-life performance per pack. Nobody neutral owns that loop today. | H |

## C. Architecture & Engineering (Farhan answers)

| # | Q · D · A | C |
|---|---|---|
| 26 | **Q:** A single FastAPI process — that's a toy. **D:** Scale-shaming. **A:** Demo topology, deliberately (36 hours, zero integration risk). The pipeline is stateless per battery — horizontal workers behind a queue is a deployment change, not a redesign. | H |
| 27 | **Q:** Postgres for telemetry time-series? **D:** DB-nerd attack. **A:** We store engineered summaries, not raw streams — that's a conscious schema decision (it's in our docs). Raw curves belong in object storage; prod adds a TSDB only if monitoring demands it. | H |
| 28 | **Q:** WebSockets die on bad networks. **D:** They watched it happen at this very event. **A:** Built a polling fallback behind a flag on day one — same event shapes, identical UI. Want me to flip it live? | H |
| 29 | **Q:** What if your model file is corrupt or wrong version? **D:** Ops maturity. **A:** Model ships as a versioned bundle; `/healthz` reports model_version and DB status; every assessment row records which version graded it. | H |
| 30 | **Q:** I could POST garbage batteries to your API right now. **D:** Security probe. **A:** Demo scope: destructive routes need a key; ingestion validates hard. Production: per-OEM API keys and BPAN-style tiered access. Auth is commodity; we spent the 36h on the engine. | H |
| 31 | **Q:** No message queue? Not a real pipeline. **D:** Buzzword test. **A:** An async background task is the right size for 847 packs; the pipeline's interface (process one battery, emit events) is exactly what a worker consumes later. We know where Kafka goes; it doesn't go in a hackathon. | H |
| 32 | **Q:** Greedy assignment is provably suboptimal. **D:** Algorithms flex. **A:** With grade gates and ~20 sites, greedy is near-optimal and explainable per-decision in stream order. Batch mode upgrade is `linear_sum_assignment` — named, understood, not needed for the demo. | H |
| 33 | **Q:** Two batteries race for the last slot at a site? **D:** Concurrency gotcha. **A:** Single worker per job processes sequentially; site capacity decrements transactionally. Boring and correct. | H |
| 34 | **Q:** Monolith? In 2026? **D:** Fashion. **A:** Modules have clean seams (services/) — it's a modular monolith. Microservices at a hackathon is how demos die; we documented that as a rule before hour zero. | H |
| 35 | **Q:** How long for 847 batteries, really? **D:** Suspects the pacing is hiding slowness. **A:** Under 5 seconds unpaced — we *slow it down* to ~2 minutes so humans can watch decisions happen. The pacing constant is an env var; want to see it raw? | H |

## D. Autonomy & Safety (Zaid/Farhan answer)

| # | Q · D · A | C |
|---|---|---|
| 36 | **Q:** "Autonomous" is marketing — this is a batch script. **D:** Brand-claim attack. **A:** The loop ingest→assess→decide→route→record runs with no human in it; the mode toggle makes approval policy explicit. Autonomy isn't magic — it's a closed loop with a ledger. A batch script doesn't explain itself or refuse unsafe actions. | H |
| 37 | **Q:** Your AI ships a fire-risk battery to a village. Who's liable? **D:** The kill-shot if unprepared. **A:** Doc 11 Q14 — safety is not ML's job: hard rules on raw data (SoH floor, IR ceiling, thermal flags) sit above the model and cannot be overridden; D-grade routes only to recyclers; dispatch needs human sign-off; every step logged. | H |
| 38 | **Q:** What if the model is *confidently wrong*? **D:** Sophisticated version of 37. **A:** Confidence gates never unlock safety gates — those run on raw measurements, not predictions. Two independent layers must both fail. | H |
| 39 | **Q:** An OEM fakes telemetry to inflate grades. **D:** Adversarial thinking — judges love it. **A:** Plausibility envelopes (capacity vs cycle count vs age) flag physically impossible stories; intake spot-audits anchor trust; and the passport makes any fraud permanently traceable to its source. Fraud-resistance by ledger. | M |
| 40 | **Q:** If it's autonomous, why is a human approving anything? **D:** Damned-either-way trap. **A:** Physical dispatch moves money and 25-kg objects; approval is a governance *choice*, configurable per operator. Regulators buy autonomy with accountability, not autonomy instead of it. | H |
| 41 | **Q:** Can an operator override a grade? **D:** Governance detail. **A:** Upgrade-direction overrides (deploying a D) are blocked, hard. Downgrade-direction (extra caution) is allowed with a logged reason. Asymmetric by design. | H |
| 42 | **Q:** Engine goes down mid-batch — what happens? **D:** Failure-mode probe. **A:** Fail-closed: unprocessed batteries stay "ingested," nothing auto-routes, job resumes idempotently. The demo reset machinery is literally this discipline productized. | H |
| 43 | **Q:** You're routing used batteries to poor villages. That's waste dumping. **D:** The most dangerous ethical reframe in the room. **A:** The opposite, and the system enforces it: only A/B grades with SoH floors and warranty-horizon RUL reach microgrids; D-grade *cannot* leave the recycling lane. Villages get certified storage at a third the cost — or no storage at all. We took that constraint seriously enough to hard-code it. | H |
| 44 | **Q:** Second-life packs failing in the field will poison trust in solar. **D:** Ecosystem-harm angle. **A:** That's why grades are conservative, RUL ships with intervals, and re-assessment is scheduled (knee alarm). Certified-with-uncertainty beats today's alternative: uncertified packs sold by weight. | H |
| 45 | **Q:** Who certifies your grades legally? Nobody. **D:** True today. **A:** Today we're decision support with an audit trail. The BPAN/AIS standardization underway is precisely the certification rail we're built to plug into — our dynamic fields map to the draft spec already. | M |

## E. Business & Market (Zaid answers)

| # | Q · D · A | C |
|---|---|---|
| 46 | **Q:** Who pays you, on day one, in rupees? **D:** Vague answer = class project. **A:** Doc 11 Q9 — fleet operators, per-pack assessment fee. They hold thousands of retiring packs and EPR liability now; a graded, passported pack resells at a multiple of scrap. | H |
| 47 | **Q:** Unit economics on a ₹8,000 scooter pack? **D:** Numbers test. **A:** Assessment is software — telemetry in, milliseconds of compute, near-zero marginal cost. If grading lifts resale by even ₹1,500–3,000 vs scrap, a ₹200–400 fee clears easily for both sides. | M |
| 48 | **Q:** Why wouldn't Ola build this internally in a quarter? **D:** Classic. **A:** Doc 11 Q8 — routing needs a *network* (many OEMs' supply × many buyers × recyclers); a neutral layer aggregates, in-house tools fragment. Same reason banks didn't each build their own UPI. | H |
| 49 | **Q:** Honest TAM? **D:** Inflated TAM = instant distrust. **A:** WRI sizes Indian second-life at ~₹8,300 crore/yr by 2030; add EPR compliance SaaS across every registered producer. We don't need a trillion-dollar slide — 2% of a real ₹8K-cr market is a company. | H |
| 50 | **Q:** Lohum is vertically integrated and 100× your size. **D:** Goliath question. **A:** Doc 11 Q6 — Lohum monetizes processing; we monetize allocation across all processors, including them. In the demo, grade-D packs route *to* a Lohum-style recycler. Neutrality is the product they structurally can't offer. | H |
| 51 | **Q:** Cold start: no OEMs → no data → no OEMs. **D:** Real chicken-and-egg. **A:** Wedge is fleet operators (own their packs, feel EPR pain today, simplest packs), not OEMs. Plus the intake lane for non-digital packs. Honest answer: this is the hard part — which is why we lead with compliance, where demand is mandated. | M |
| 52 | **Q:** This is a hackathon project pretending to be a startup. **D:** Tone attack. **A:** Correct — 36 hours old. What's not pretend: the regulation (dated), the market sizing (WRI), the working loop you just watched. We de-risked the product question; the company question is next. | H |
| 53 | **Q:** OEMs will give grading tools away free. **D:** Pricing-power attack. **A:** An OEM grading its own packs is a seller grading its own goods — buyers will demand neutral certification, like used-car inspection. Free-but-conflicted loses to paid-but-neutral in any market with information asymmetry. | H |
| 54 | **Q:** Why won't CPCB just build this into the EPR portal? **D:** Government-competition fear. **A:** Governments build registries, not optimization engines — and the BPAN draft explicitly envisions private service providers updating dynamic data. We'd integrate with the portal, not compete with it. | H |
| 55 | **Q:** Exit story? **D:** Investor cosplay. **A:** Registry network → outcome-data moat → the standard grading layer. Natural acquirers: OEM alliances, energy majors, or the processors themselves. But the honest answer is: pilot first, exit slides later. | M |
| 56 | **Q:** Why India-only? Isn't this bigger? **D:** Ambition probe (or trap). **A:** India-first because the regulatory clock (EPR now, BPAN 2027) and the 2W/3W fleet structure are unique advantages here. The engine ports to the EU's 2027 passport mandate unchanged — same architecture, different ID format. | H |
| 57 | **Q:** Four students vs an industry. **D:** Credibility. **A:** The incumbents are conflicted (processors want packs cheap, OEMs want grades high) — the neutral layer almost has to come from a new player. And we just built in 36 hours what the draft regulation describes for 2027. | M |

## F. Competition & Moat (Zaid answers)

| # | Q · D · A | C |
|---|---|---|
| 58 | **Q:** What's your moat, in one sentence? **D:** Rambling = no moat. **A:** The closed loop of predicted-vs-actual second-life outcomes per battery, accumulated neutrally across OEMs — data nobody else is positioned to collect. | H |
| 59 | **Q:** Tata Elxsi already demoed Battery Aadhaar with NITI Aayog. **D:** "You're late" — most dangerous competitive fact in the room. **A:** Doc 11 Q7 script — that's the identity layer; we compute the dynamic fields it stores and make the decisions it records. Passports record history; VoltLife writes the next chapter. Our IDs follow their draft format on purpose. | H |
| 60 | **Q:** EU passport vendors (Circulor et al.) will land in India. **D:** Global-player threat. **A:** Same answer as Elxsi: traceability ≠ decisions. Plus India-specific duty cycles, chemistry mix, and the informal-sector intake problem — local models and local rails matter here. | M |
| 61 | **Q:** A consultant with Excel does this today. **D:** Dismissive reduction. **A:** Not at 128 GWh, not in milliseconds, not with quantified uncertainty and an audit trail per pack. Excel doesn't scale, explain, or remember. | H |
| 62 | **Q:** It's open-sourceable — anyone clones it next week. **D:** Defensibility. **A:** The code, sure. The registry, the accumulated outcome data, and operator trust don't clone. We'd open-source parts deliberately to become the standard. | H |
| 63 | **Q:** If it's so obvious, why hasn't anyone done it? **D:** The "you must be missing something" classic. **A:** Until 2022 there was no forcing function; until the BPAN draft there was no standard identity. The data was siloed and the obligation didn't exist. Both changed within the last 36 months — that's the *why now*. | H |
| 64 | **Q:** CATL and Chinese second-life platforms will enter. **D:** Geopolitical scale threat. **A:** Battery data is critical-infrastructure data; localization and domestic-champion dynamics strongly favor an India-resident stack — see PLI's local-value mandates. | M |
| 65 | **Q:** The BPAN final spec will differ from the draft you built on. **D:** Building-on-sand. **A:** Certain — that's why the ID module is one isolated service; spec change = remap fields. The engine (assess/decide) doesn't care what the ID looks like. EPR obligations exist regardless. | H |
| 66 | **Q:** Any IP? **D:** Expects bluff. **A:** None in 36 hours, and we won't pretend otherwise. Defensibility here is data + execution + standard-setting, not patents. | H |
| 67 | **Q:** Who's your real competitor? **D:** Tests self-awareness. **A:** The status quo: informal scrap channels paying cash today, no questions asked. Beating "do nothing" is the actual fight — which is why the compliance wedge matters more than any startup rival. | H |

## G. Sustainability & Impact Math (anyone, drilled)

| # | Q · D · A | C |
|---|---|---|
| 68 | **Q:** How much of the demo's impact is real? **D:** Honesty test, pass/fail. **A:** Real math on a simulated fleet — formulas and factors cited in the repo, fleet labeled simulated on the slide. Plug in real telemetry and only the inputs change. | H |
| 69 | **Q:** Where does 60 kg CO₂e/kWh come from? **D:** Made-up factor = dead. **A:** Doc 11 Q16 — published cradle-to-gate range is ~48–120 (median ~80); we chose below-median deliberately. Citations are in the repo and on this phone. | H |
| 70 | **Q:** Second-life storage doesn't displace new manufacturing 1:1. **D:** Economically sophisticated. **A:** Agreed — substitution is partial; the conservative factor absorbs much of that, and the formula is one constant anyone can re-run with their own elasticity. We'd rather under-claim and show the dial. | M |
| 71 | **Q:** You ship 25-kg packs 1,000 km — transport emissions? **D:** Gotcha with a number. **A:** Road freight ≈ 0.06–0.1 kg CO₂e/tonne-km → a pack at 1,000 km ≈ 2–3 kg, vs ~200 kg credited. The optimizer's distance term suppresses it anyway; netting it explicitly is a one-line roadmap item. | H |
| 72 | **Q:** You're delaying recycling, not solving anything. **D:** Reframe of the core thesis. **A:** Delay *is* the value: 4–6 years of clean storage service from hardware that already exists — then the same pack enters recycling through the same ledger. Cascade-then-recycle is strictly better than recycle-now; BWMR itself includes refurbishment. | H |
| 73 | **Q:** Used batteries in rural microgrids undermines reliability — anti-SDG7. **D:** Twin of #43, impact flavor. **A:** Grade floors, intervals, scheduled re-assessment — certified second-life vs the actual alternative, which is no storage or uncertified scrap. Cost per kWh at a third makes grids viable that otherwise aren't built. | H |
| 74 | **Q:** "Equals 6,300 trees" — greenwashing. **D:** Translation backfire. **A:** Primary metrics are MWh and tCO₂e with formulas one click away; equivalences are an optional translation layer, clearly labeled. Math first, metaphor second. | H |
| 75 | **Q:** Recycling is good — why is "premature recycling" bad? **D:** Counterintuitive framing risk. **A:** Recycling an 80%-SoH pack discards years of service to recover ~90% of materials at high energy cost. Use, *then* recycle — recovery happens either way; service only happens if you don't skip it. | H |
| 76 | **Q:** Your counter shows lifetime MWh as if delivered today. **D:** Inflation accusation. **A:** Labeled "projected lifetime MWh unlocked" with the formula on the methodology card; instantaneous usable kWh shown alongside. Both numbers, honestly named. | H |
| 77 | **Q:** What's the footprint of running your own platform? **D:** Mirror test. **A:** Millisecond tree inference, no LLM in the decision loop, one server. Negligible against tonnes avoided — and a pointed contrast with GenAI-heavy builds. | H |
| 78 | **Q:** Five SDGs claimed — SDG-washing. **D:** Logo-soup accusation. **A:** We *lead* with three and show the mechanism for each on screen (storage cost ↓, circularity, avoided emissions). The other two are honest side effects, one slide, three seconds. | H |
| 79 | **Q:** EPR certificates in India are riddled with fraud — you'll launder it. **D:** Sector-scandal awareness. **A:** Opposite: per-pack ledger with hash-chained events makes every EPR claim auditable down to the battery. We make fraud harder, not easier — that's a selling point to CPCB. | H |

## H. Regulatory & India Context (Zaid answers)

| # | Q · D · A | C |
|---|---|---|
| 80 | **Q:** BWMR sets recycling targets — does the law even want reuse? **D:** Regulatory-literacy test. **A:** The Rules explicitly cover refurbishment and second-life routing before recycling, plus recycled-content mandates from FY28. Cascade feeds the recycling chain; it doesn't dodge it. | H |
| 81 | **Q:** BPAN is a draft, not law. **D:** Sand-foundation. **A:** Draft with a ministry, a committee, and a 2027 target — and EPR is already binding law regardless. We track the draft; if fields move, we remap one module (#65). | H |
| 82 | **Q:** "Aadhaar" is a government brand — trademark problem? **D:** Legal curveball. **A:** It's the government's own name for the battery scheme — we implement their nomenclature. Commercially we'd brand as VoltLife Passport, BPAN-compatible. | H |
| 83 | **Q:** Centre vs state jurisdiction chaos? **D:** Indian-federalism reality. **A:** Our anchor is the central CPCB EPR portal and MoRTH's BPAN — both central. State-level waste rules affect logistics partners, not the intelligence layer. | M |
| 84 | **Q:** Moving used Li-ion is hazmat — e-waybills, transport rules. **D:** Operational gotcha. **A:** True friction, and exactly why a decision layer helps: compliance constraints become routing constraints (licensed transporters, distance caps). Encoded policy beats tribal knowledge. | M |
| 85 | **Q:** Data localization requirements? **D:** Compliance probe. **A:** India-resident deployment by default; tiered access mirrors the BPAN draft's public/private split. | H |
| 86 | **Q:** Why no government partnership if it's so aligned? **D:** Wants you overreaching. **A:** Deliberate: we built only on *published* specs and public datasets so nothing requires permission to start. Alignment without dependency. | H |
| 87 | **Q:** The informal sector — kabadiwalas — will outbid your channel in cash. **D:** Hardest India-reality question. **A:** You don't beat the informal sector with enforcement, you beat it with economics: grading lifts pack value above scrap-cash, so formal intake pays *more*. Formalization through price, with the informal aggregators as intake partners, not enemies. | M |

## I. Demo & Authenticity (whoever is driving)

| # | Q · D · A | C |
|---|---|---|
| 88 | **Q:** Is any of this live, or is it a video? **D:** Direct authenticity challenge. **A:** Live — pick any battery and I'll open it; or hand me a fresh CSV. (Replay mode exists as a fallback and we'll say so if we use it.) | H |
| 89 | **Q:** Why exactly 847? **D:** Smells staged. **A:** A plausible quarterly retirement batch for a mid-size fleet — and big enough to prove streaming decisions at scale. Honest answer: it also demos beautifully. | H |
| 90 | **Q:** The map arcs are decoration. **D:** Style-over-substance jab. **A:** Every arc is a row in the deployments table — click it: site, score, three reasons, distance. Decoration doesn't have foreign keys. | H |
| 91 | **Q:** Did AI write this codebase? **D:** 2026's favorite gotcha. **A:** We used AI tooling like every modern team — and we own every design decision: ask any of us about our module's tradeoffs. The 13-doc plan in the repo *was* the spec we held the tools to. | H |
| 92 | **Q:** What actually broke during the build? **D:** Tests honesty; "nothing" = lying. **A:** Tell the true story (decided post-event — likely the WS/integration or model-swap moment), what it cost, how the fallback caught it. Authentic battle scars score. | M |
| 93 | **Q:** Show me the model code right now. **D:** Bluff-call. **A:** Repo's open — predictor.py, training notebook, CV results. Razi walks features while it's on screen. | H |
| 94 | **Q:** One more week — what do you build? **D:** Vision-and-priorities test. **A:** Outcome feedback loop (field telemetry from deployed packs), LFP dataset expansion, EPR report e-filing. In that order, because data moat > features. | H |
| 95 | **Q:** Why should you win over the team next door? **D:** Direct, common, fumbled often. **A:** This is the only project in the room where real ML, national policy hooks, and measurable impact run as one live loop — graded, explained, and honest about what's simulated. | H |

## J. Team & Execution (everyone, 20 s each)

| # | Q · D · A | C |
|---|---|---|
| 96 | **Q:** Four people, five modules — who built what? **D:** Exposes passengers. **A:** Ownership map is in the README: Zaid architecture/integration, Farhan backend/engine, Zaki experience, Razi ML. Ask any of us anything in our lane. | H |
| 97 | **Q:** Hardest technical decision? **D:** Judgment probe. **A:** Killing PyTorch for boosted trees, and building replay infrastructure before features. Both were bets on *finishing* — judgment over fashion. | H |
| 98 | **Q:** Delete your ML model right now — what survives? **D:** AI-necessity stress test. **A:** Ingestion, passports, and the ledger run; grading and deployment *stop*. The system halts exactly where intelligence sits — that's the proof AI is load-bearing, not garnish. | H |
| 99 | **Q:** What happens to this after Sunday? **D:** Detects demo-and-dump. **A:** Pilot conversation with a fleet operator is the single next step; modules map to owners. No grand promises — one pilot. | M |
| 100 | **Q:** What did you cut, and why? **D:** Scope-discipline test. **A:** SitesView page, marketplace ideas, blockchain, route planning — pre-agreed cut-lines in the plan, decided before hour zero so 2 a.m. us couldn't negotiate. | H |
| 101 | **Q:** Biggest weakness — and don't say "we care too much." **D:** Honesty under pressure. **A:** Doc 11 Q18 — data access. The model is only as good as telemetry OEMs share; the compliance wedge exists precisely because that's the hard part. | H |
| 102 | **Q:** One sentence. Why does VoltLife matter? **D:** The elevator kill-shot; rambling = forgettable. **A:** "India has mandated every battery an identity — we built the intelligence that decides its future, and you just watched it run." | H |

---

## Drill protocol

- **H24 drill:** all Medium/Low rows (7, 8, 11, 12, 20, 21, 39, 45, 47, 51, 55, 57, 60, 64, 70, 83, 84, 87, 92, 99) — these are where exact wording matters.
- **H32 drill:** rapid-fire 20 random questions, 20-second cap, one voice each.
- Rule: never answer outside your lane; hand off by name ("Razi takes data questions").
- If a judge lands a hit we have no answer for: "We didn't get to that in 36 hours — here's how we'd approach it." Then approach it. Honesty is the only fallback that never breaks.
