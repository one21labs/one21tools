# Tiered-execution benchmark — 2026-07-10 (issue #41)

Does a tiered configuration (Sonnet plans + validates, Haiku implements, re-dispatch <=3 cycles)
match Sonnet-solo quality at materially lower cost/time? Pre-registered in issue #41; verdict
methodology: ADR 0019 (clustered CI), ADR 0023 (hermetic executor + auditable raw), ADR 0024
(cost-justification), ADR 0025 (fraction-met headline), ADR 0026 (artifact formats).

## Verdict

**REJECT the tiered configuration — decisively.** It fails BOTH halves of the pre-registered rule:

- **Quality:** tiered fraction-met is exactly Haiku-solo's (delta -0.000, CI [-0.097, +0.097]) —
  the Sonnet plan+validate loop added nothing over its cheap worker. Vs Sonnet-solo the delta is
  **-0.282, 95% CI [-0.418, -0.145]** — materially inferior, far past the -0.05 margin.
- **Cost:** tiered runs **8.8x** Sonnet-solo's median tokens, **4.1x** its USD, **4.8x** its
  wall-clock (rule required <= 0.7x). The orchestration tax bought negative value.

| Arm | frac-met | binary pass | med tokens/cell | med USD/cell | med wall/cell |
|---|---|---|---|---|---|
| haiku-solo | 0.315 | 0.000 | 35,912 | $0.016 | 24.6s |
| sonnet-solo | 0.597 | 0.042 | 23,026 | $0.055 | 32.0s |
| opus-solo | 0.601 | 0.000 | 30,203 | $0.173 | 41.2s |
| tiered | 0.315 | 0.042 | 203,163 | $0.225 | 153.7s |

**The "real prize" question inverts:** Opus-solo quality at sub-Opus cost is already delivered by
**Sonnet-solo** (opus-sonnet delta +0.004, CI [-0.082, +0.090], at 3.2x the USD) — not by tiering.
Sonnet-solo is the quality-cost frontier on these tasks. The Opus-main tiered variant is moot:
the pre-registration sequenced it after a Sonnet-main success, which did not occur.

**Why the loop failed (mechanism, from the traces):** 18/24 tiered chains hit the 3-cycle cap and
17/24 ended with the validator still rejecting — Haiku could not satisfy the Sonnet validator's
defect lists within the cap, and the final artifact ships regardless (pre-registered). The
validator itself showed a 25% false-accept rate vs the blind grader (6/24 accepted cells the
grader failed; 0 false-rejects), so even its acceptances were unreliable. Iterating a weak
implementer against a strong critic converged to the implementer's ceiling, not the critic's.

**Binary pass floored again** (2/96 cells) exactly as in 2026-07-08-skills-hermetic; per ADR 0025
fraction-met is the powered headline and the pre-registered pass-rate margin is vacuously
satisfied at the floor (its "non-inferiority: True" carries no signal — reported for
completeness, not relied on).

## Method

- **Arms (per issue #41):** haiku-solo / sonnet-solo (baseline) / opus-solo (ceiling) / tiered
  (Sonnet plans -> Haiku implements -> Sonnet validates -> re-dispatch with defect list, <=3
  worker cycles, last artifact ships). One `claude -p` per role-call, CLAUDE_EFFORT=medium,
  identical NEUTRAL framing every call in every arm (role instructions ride the user prompt).
- **Hermetic executor (ADR 0023, unchanged from 2026-07-08-skills-hermetic):** external empty
  cwd, Skill/Task/file/exec tools denied, user ~/.claude/CLAUDE.md relocated. Tasks are
  text-artifact-shaped, so the full tool-deny carries over; the tiered validator sees ONLY the
  task + plan + deliverable, never the grading expectations (tiered.py never opens meta.json).
- **Tasks:** 16 implementation-shaped candidates from the live skills/*/evals/evals.json
  (artifact-producing prompts; prep.py holds the inclusion rule). Pre-screen 1-rep Haiku vs Opus
  (escalated to rep 2 for the 8 zero-gap ties, per the pre-registered sequential-escalation
  rule) selected the 8 with a positive Haiku->Opus fraction-met gap (+0.10..+0.83); saturated
  and negative-gap tasks dropped. Main grid: 8 tasks x 4 arms x 3 reps = 96 cells.
- **Grading:** blind (arm withheld; graded/items carry prompt + expectations + response only),
  each expectation MET/NOT-MET strictly, adversarial prosecutor re-count on every PASS
  (grade.workflow.js, prompts verbatim from 2026-07-08-skills-hermetic).
- **Cost accounting:** total tokens/USD/wall summed across ALL calls in a configuration
  (tiered = plan + every implement + every validate; the tiering tax counts). Solo cells pay the
  same per-call CLI overhead, so the comparison is configuration-fair.

## Pre-registered owner calls, resolved (issue #41 execution-design comment)

1. **Grader independence:** unsatisfiable with 3 executor tiers exhausting haiku/sonnet/opus —
   the Sonnet-grades-Sonnet residual is accepted per ADR 0019 precedent (skills-hermetic graded
   sonnet-on-sonnet), mitigated by blinding + uniform prosecution. Direction of the residual
   (if any) favors Sonnet-family arms, which only strengthens the tiered rejection: the losing
   arm's validator WAS Sonnet.
2. **Hermetic controls:** carried over wholesale — the "tool-deny impossible" concern dissolved
   because the existing eval sets are text-artifact-shaped, exactly as the pre-registration's
   task source implied.
3. **Retry cap / feedback format:** 3 worker cycles (pre-registered); validator returns strict
   JSON {pass, defects[]}; on FAIL the worker gets task + plan + its previous attempt + the
   defect list. Unparseable validator JSON = accept-and-stop, recorded (0 occurred).

## Caveats

- A refusal mode ("headless session, can't write files") appears in a minority of cells across
  arms (both graded 0 by rule); it is part of the measured behavior under identical framing.
- n=8 tasks: per-task CIs are wide, but the headline deltas clear their margins by multiples.
- The tasks are single-file text artifacts; a tool-using, multi-file implementation loop could
  behave differently — that would be a different (new) benchmark, not a rerun.

## Reproduce / audit

```
python3 prep.py                                   # prompts/, meta.json, candidates.txt from live evals
KEYS=candidates.txt ARMS="haiku opus" REPS=1 OUT=$PWD/prescreen/outputs \
  HERMETIC_RELOCATE_USER_MEMORY=1 bash harness.sh # pre-screen (escalate ties to rep 2, see escalate.txt)
OUTDIR=$PWD/prescreen/outputs GRADEDIR=$PWD/prescreen/graded python3 blind.py
# Workflow grade.workflow.js {itemsDir, bids}      -> verdicts.jsonl ; then python3 prescreen_select.py
HERMETIC_RELOCATE_USER_MEMORY=1 bash harness.sh   # main grid (tasks.txt, 4 arms, 3 reps)
python3 blind.py                                  # -> graded/items (arm withheld)
# Workflow grade.workflow.js {itemsDir, bids}      -> graded/verdicts.jsonl (grade + prosecute)
python3 aggregate.py                              # -> results.jsonl + the tables above
python3 pack.py ; DIR=prescreen python3 pack.py   # ADR 0026: costs.csv (+ traces.jsonl) + raw.tar.gz
```

`outputs/*.txt` are the raw responses (every graded cell plain on main — this benchmark's ADR
0023 sample; `sample_rule` in metadata.json). `graded/verdicts.jsonl` holds the non-derivable
LLM judgments; `costs.csv`/`traces.jsonl` the flat call records; everything else regenerates.
