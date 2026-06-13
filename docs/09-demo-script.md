# 09 — Demo Script & Build Plan (Owner: Zaki experience · Zaid narration)

One unforgettable demo beats ten unfinished features. Budget: **3 minutes of demo inside a ~5-minute slot.** Rehearse until the clicks are muscle memory — minimum 3 full dry runs (doc 10 schedules them).

## Pre-flight (15 min before, every time)

`/healthz` green · `POST /demo/reset` · CommandCenter open, map centered on India · feed empty · counters zero · `sample_fleet.csv` on desktop · backup laptop with replay mode tested · phone hotspot on standby · projector resolution checked · volume of confidence: maximum.

## The script

**[0:00 — Hook, map dark]**
> "By 2030, India will retire **128 gigawatt-hours** of lithium batteries — that's NITI Aayog's number, not ours. Most still hold 70–80% of their capacity. Today, nobody decides what happens to each one. So we built the system that does."

**[0:20 — Ingest]**
> "This is a simulated retirement batch — 847 packs, the kind a fleet operator like Ola or Ather retires in a quarter, with degradation profiles drawn from real NASA battery data."

*Drag CSV into Upload Wizard → preview → hit LAUNCH. Switch to Command Center.*
⚠️ Never claim the batch is real OEM data. "Simulated batch, real physics" is the honest flex.

**[0:35 — The cascade (let it breathe, ~60s)]**
Markers pop in grade colors, feed scrolls, counters climb.
> "Every battery: graded by ML trained on NASA and CALCE datasets. State of Health. Remaining useful life — **with confidence intervals**. And the why: low thermal stress, stable voltage, knee not yet reached. Then the deployment engine takes over —"

*Arcs start shooting battery→site.*
> "— Grade A packs to solar storage in Rajasthan. Grade B to rural microgrids in Bihar. And Grade D? **Hard safety rule — straight to certified recyclers. The AI cannot deploy a dangerous battery.** Every decision: three reasons, logged."

**[1:45 — Battery Aadhaar]**
*Click one battery → passport page.*
> "Each battery gets a Battery Aadhaar — modeled on MoRTH's draft Battery Pack Aadhaar spec, the 21-character ID India is rolling out in 2027. Static data on the QR; dynamic data — health, status — on the server. We didn't invent the passport. **We built the brain that fills it in and acts on it.**"

*Point at decoded ID segments, scroll the lifecycle timeline manufacture → EV → assessment → solar farm.*

**[2:25 — Impact close]**
*Open `/impact`, counters land.*
> "One batch: **~2 gigawatt-hours unlocked, ~140 tonnes of CO₂e avoided, 700 batteries diverted from premature recycling** [read live numbers]. India retires 128 GWh by 2030. Multiply."

**[2:45 — One-liner]**
> "VoltLife. Every battery deserves a second life — and now there's a system that decides it."

## Hardware (UART) — gated side-quest

Only if it passed two clean rehearsals by H24 (doc 12 gate). If it lives: 15-second beat after the cascade — "and this isn't just CSVs — here's a real pack streaming over UART into the same pipeline." If it dies: it never existed; the demo loses nothing. Never debug hardware on stage.

## Demo build plan (engineering for the above)

| Beat | Needs | Owner | Fallback |
|---|---|---|---|
| Hook | none (talk over dark map) | Zaid | — |
| Ingest | UploadWizard + `/ingest` | Zaki/Farhan | pre-staged `job_id`, narrate over it |
| Cascade | WS feed + pacing + markers/arcs/counters | all | polling flag → replay mode → **backup video** |
| Aadhaar | passport endpoint + page | Farhan/Zaki | pre-loaded battery detail tab |
| Impact | `/impact` page | Zaki | final-state screenshot slide |

Pick the "hero battery" for the Aadhaar beat **in advance** (clean grade-A with a pretty timeline; note its ID). Never live-pick from 847 rows on stage.

**Backup video:** screen-record the full happy path at H30 (OBS or phone). Judges forgive "here's the recording while I fix Wi-Fi" — they do not forgive five minutes of dead air.

## Q&A demo ammo

Keep open in tabs: a grade-D battery passport ("safety rail" proof) · the explainability panel of a low-confidence battery ("model knows what it doesn't know") · `/sites` or impact breakdown ("recyclers are nodes — Lohum is a customer, not a competitor").
