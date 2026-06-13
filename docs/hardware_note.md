# Hardware Note — Live Telemetry Rig (formal status: OPTIONAL BONUS)

## Status, stated plainly

- **Hardware is optional.** It is a bonus demonstration capability, nothing more.
- **Core VoltLife functionality does not depend on hardware in any way.** The pitch, the demo, and every feature work identically without it.
- **Hardware data enters through the standard ingestion path** — the bridge script POSTs a JSON battery record to the existing `POST /api/v1/batteries/ingest`. No special endpoint, no special handling. "The real pack enters through the same front door as the CSVs" is itself the demo line.
- **The stage gate stands (docs/12 R5):** two clean rehearsals by H24, or the rig stays in its box and is never mentioned.

## Components

| Part | Role |
|---|---|
| ESP32 | Microcontroller; reads sensors, streams over native USB serial to the laptop |
| INA219 | Voltage + current sensing; current integrated over a discharge session → capacity estimate (coulomb counting) |
| DS18B20 | Cell temperature |
| 18650 cell + holder | The battery under test — same form factor and chemistry class as the NASA training data (genuinely in-distribution) |

Plus: a small discharge load for the measurement session, a spare 18650, and the laptop-side bridge script (~40 lines: read serial → assemble JSON record → POST to ingest). Bridge script is Razi's, written only if the gate is attempted.

## What the rig can and cannot honestly provide

It measures a **snapshot**: live voltage, current, temperature, and a session-estimated capacity. It cannot provide cycle history — so of the 14 ML features it honestly populates ~4–5; cycle count is operator-entered; the 6 history features arrive as NaN. Consequence: the live battery will assess at **medium/low confidence — correctly.**

## The framing decision (made here, per audit fix S4)

**Adopted: Option 1 — the governance story.** On stage (if the gate passes): *"This is a real cell streaming live telemetry. It has limited history, so watch what the system does: medium confidence, routed for inspection rather than deployment. The model knows what it doesn't know."* This turns the physical limitation into a demonstration of the confidence engine and the inspection queue (judge_attacks #5) at zero extra build cost.

Explicitly rejected: pre-filling synthetic history to force a confident grade while implying full live measurement. If history is ever pre-filled for a rehearsal, the on-stage description must say so.

## What this note does NOT do

No architecture changes, no new endpoints, no schema changes, no new features. This document only formalizes the rig's status, its data path, and the honesty rules around it.
