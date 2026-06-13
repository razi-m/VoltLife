# 12 — Risk Register, Fallbacks & Submission Checklist (Owner: Zaid)

## Risk register

| # | Risk | Likely? | Impact | Trigger | Mitigation / Fallback | Owner |
|---|---|---|---|---|---|---|
| R1 | Behind schedule at M3 (H18) | Med | High | Milestone slips >2h | Cut-line 1: drop SitesView; simplify deployment scoring to gates+distance | Zaid |
| R2 | Venue Wi-Fi breaks WS / deploys | **High** | High | First WS drop | Polling flag (built day 1) → localhost demo → phone hotspot | Zaki |
| R3 | Live inference misbehaves on stage | Low | Fatal | Any anomaly in dry run #2 | `/demo/replay` (pixel-identical) → backup video | Farhan |
| R4 | Model outputs absurd values on synthetic fleet | Med | High | QA sweep at H20 finds SoH/RUL nonsense | Clamp outputs to sane ranges + fix generator jitter; hero battery pre-picked regardless | Razi |
| R5 | UART hardware fails | High | Low (it's bonus) | Fails either rehearsal by H24 | Gate: cut silently; demo never references it | Razi |
| R6 | Railway/Render down or sleeping during judging | Med | Med | `/healthz` red at pre-flight | Primary demo is localhost; deployed URL only for submission + QR | Farhan |
| R7 | "2-day" window is shorter than 36h | Med | High | Kickoff announcement | Compressed plan in doc 10 (freeze H20) | Zaid |
| R8 | Judge knows BPAN/Tata Elxsi → "this exists" | Med | High | Q&A | Scripted answer (doc 11 Q7); we implement the draft spec + add intelligence | Zaid |
| R9 | Judge attacks fabricated-looking stats | Med | High | Q&A | All pitch numbers are cited (doc 01 sources); fleet explicitly labeled simulated | All |
| R10 | A teammate is sick/absent | Low | High | — | Every module has a documented contract (docs 03–08); Zaid is backup for Farhan, Razi for Zaid's deck | Zaid |
| R11 | CSV edge cases crash ingestion on stage | Med | High | Upload fails in rehearsal | Strict template + reject report (never 500); demo uses the exact rehearsed file | Farhan |
| R12 | Demo overruns the slot | Med | Med | Dry run #1 timing | PACE_S env var shortens cascade; cut FleetTable beat first; hard 3-min demo cap | Zaid |
| R13 | Counters end on implausible numbers (too big/small) | Med | Med | H24 seed sanity check | Tune generator mix; cross-check vs doc 06 worked example | Razi |
| R14 | Laptop dies / projector handshake fails | Low | Fatal | Pre-flight | Backup laptop with full local stack + replay + video; HDMI and USB-C adapters packed | Zaki |

## Standing rules

- Every fallback is **built and rehearsed**, not theoretical. Untested fallbacks are decorations.
- Demo machine: airplane-mode-proof — full stack runs offline except map tiles; **cache tiles by panning India at every zoom used in the demo while online** (Leaflet keeps them for the session), or keep the map at fixed zoom where tiles are loaded.
- After H30, the only allowed git commands are for the README. Code freeze means freeze.

## Final submission checklist (complete by H33)

**Devfolio**
- [ ] Project name: VoltLife — The Battery Lifecycle Operating System
- [ ] Tagline: "India retires 128 GWh of batteries by 2030. VoltLife decides what happens to every single one."
- [ ] Problem / solution write-up (lift from doc 01; cite NITI Aayog, BWMR, BPAN)
- [ ] Tech stack listed (React, FastAPI, PostgreSQL, scikit-learn, SHAP, Leaflet)
- [ ] "Challenges we ran into" — tell the cell-vs-pack data story honestly; judges read this
- [ ] Demo video link (the H30 recording — upload unlisted YouTube early, processing takes time)
- [ ] Deployed URL + `/healthz` green at submission time
- [ ] Repo public, with README below
- [ ] Track/prize selections reviewed (check sponsor prizes: relevant ones only — don't tick ETHIndia unless the on-chain anchor stub is real)

**Repo README must contain**
- [ ] 90-second GIF of the cascade (judges who never visit your table still see the demo)
- [ ] Architecture diagram (doc 02 mermaid renders on GitHub)
- [ ] "Real vs simulated" table (doc 01) — pre-empting skepticism in writing
- [ ] Model card: datasets, features, leave-one-cell-out MAE, assumptions (300 cycles/yr, 60 kg CO₂e/kWh + citations)
- [ ] Run instructions (one command per service) + seeded demo credentials/key
- [ ] Team + module ownership

**Physical kit for demo day**
- [ ] Both laptops charged + chargers · HDMI/USB-C adapters · phone with hotspot + charged power bank
- [ ] UART rig in a box (only emerges if gate passed) · printed hero-battery QR card (judges scan it → live passport — small prop, big effect)
- [ ] Water. Seriously.

## The one-sentence risk philosophy

Everything on stage has a tested understudy: WS→polling→replay→video; cloud→localhost; live-pick→hero battery. The demo cannot die twice.
