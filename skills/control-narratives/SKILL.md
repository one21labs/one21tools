---
name: control-narratives
description: Invoke when writing, reviewing, or templating control narratives, FRS/FDS, or sequence/interlock documentation for industrial control (PLC, DCS, SCADA). Apply ISA-5.06.01 structure, ISA-106 states, STE wording, and the SSoT check before presenting.
---

# Control Narratives

Treat the narrative as a requirements document: every statement testable at FAT, every number from the input, every behavior traceable from design basis to test procedure.

## Standards stack

| Layer | Standard | Owns |
|---|---|---|
| Skeleton | ANSI/ISA-5.06.01-2007 | Module partitioning, tag database, interlock matrix, sequence tables |
| Behavior | ANSI/ISA-106.00.01-2023 (+ TR106.00.01-2013, TR106.00.02-2017) | States, transitions, hold/abort, automation level per task |
| Sentences | ASD-STE100 Issue 9 (Jan 2025) | Narrative text, step descriptions, prompts, warnings |
| Alarms | ISA-18.2 | Referenced alarm database, not restated |
| SIS | IEC 61511 SRS | Separate document; BPCS narrative references only |

ISA-106 covers continuous processes at ISA-95 levels 1-2. Batch goes to ISA-88.

## Document hierarchy

| Level | Document | Answers | Owner |
|---|---|---|---|
| Plant-wide | Control philosophy | Shared rules: modes, alarm philosophy, fail-safe conventions, HMI standards | Controls lead |
| Per module | Control narrative / FRS | What the system must do | Process writes, controls reviews |
| Per module | Software design spec | How code implements it | Integrator |
| Verification | FAT/SAT procedures | Proof it does it | Integrator, owner witnesses |

Do not put implementation detail (blocks, tasks, routines) in the narrative.

## Narrative template (one per equipment module)

1. Purpose and boundaries: function, upstream/downstream interfaces.
2. Equipment, tags, setpoints: reference the instrument index; do not copy it. Give a setpoint table (ID | Function | Value | Action | Basis | Owner) for every number the logic uses.
3. States and transitions: ISA-106 state table with allowed transitions, permissives, initiator (operator/auto), and automation level (manual, operator-prompted, automatic).
4. Regulatory control: per loop give PV, output, action, mode behavior, cascade/override. No tuning values.
5. Sequences: step tables with columns Step | Action | Transition condition | Timeout | Failure response.
6. Interlocks and permissives: per interlock give cause, effect, latched or auto-reset, reset method, and fail position. Cite the cause-and-effect chart row too, never instead.
7. Alarms: reference the rationalized alarm database.
8. Abnormal handling: bad PV, comms loss, power loss and restart, fail positions.
9. Operator interface: what the operator sees, changes, and is prompted for.
10. Open items: each with owner and due date.

Choose state-based control (SBC) for plant/unit modes; sequence-based control (SqBC) for discrete jobs (compressor start, purge).

## Rules

- Write behavior out: what trips, what stops, latched or auto-reset, reset method, fail position, Hold/Abort response. Never defer logic to a document the narrative does not contain.
- Take numbers only from the input. A missing value becomes a setpoint row with no value, cited by ID: `SP-07 | LT-201 high-high | HOLD | basis: overfill study | owner: process`, then "LT-201 above SP-07".
- Never propose a safety or trip value, not even as provisional or "to confirm".
- Give every requirement an ID (FR-<module>-NNN). If it cannot be tested, rewrite or remove it.
- Specify transitions, timeouts, and restarts as fully as steady state.
- Use tag numbers, not descriptive equipment names alone.
- Require operations sign-off on states and prompts.
- After construction starts, change only through MOC with revision clouds and a change log.

## STE wording (ASD-STE100)

- Procedural sentences 20 words max; descriptive 25 max.
- One instruction per sentence, imperative, active voice.
- One word, one meaning. Approved dictionary words plus project technical names.
- Warnings and cautions: command first, then reason, placed before the affected step.
- Paragraphs 6 sentences max, one topic.

Example:
- Before: "Upon confirmation of suction pressure being established, the operator should initiate the compressor start sequence."
- After: "Make sure that PT-101 is above the start permissive. Push START on the K-100 faceplate."

Apply STE as an editing pass after the engineering content is settled.

## Workflow

Writing: build the ISA-106 state/transition table first, derive 5.06 sequence tables from it, then write prose, then STE pass.

Reviewing: run the checks below and report findings as a table: ID | Location | Issue | Fix.

## Checks before presenting

- [ ] Every number is from the input; every missing one is a blank setpoint row, cited by ID
- [ ] No logic deferred to a document the narrative does not contain
- [ ] Every requirement has an ID and a test method
- [ ] Every state has entry permissives and allowed exits
- [ ] Every sequence step has a timeout and failure response
- [ ] Bad PV, comms loss, power loss/restart, fail positions defined
- [ ] Interlock behavior written out; alarms referenced, not duplicated
- [ ] SIS functions referenced to the SRS, not specified here
- [ ] STE limits met (sentence length, one action, active voice)
- [ ] Open items listed with owner and date
