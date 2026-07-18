# 2026-07-17 code-standards re-measure (#214) — L1: ADOPT v2; L2: KEEP (strong, judge-robust)

Canonical re-measurement with the shipped skill-bench harness (owner direction on #214: the
13-Jul worktree campaign is a lead, not evidence). Pre-registration: `metadata.json`, committed
before any generation. Run was owner-stopped mid-grid on 17-Jul and resumed same day
owner-directed; checkpoint state and resume steps are on the issue.

## L1 — trigger ablation (matched protocol, within-run A/B only)

| variant | durable should-fire | durable FP | durably lost |
|---|---|---|---|
| control (live description) | 6/8 | 0/8 | "add a proper header comment...", "is this function doing too many things at once" |
| **v2** | **8/8** | **0/8** | none |

- The 13-Jul 4/8 lead did NOT reproduce (control = 6/8 under the current harness), but two
  should-fire queries were durably lost — the under-trigger is real, smaller than the lead.
- **ADOPT v2** — all three pre-registered prongs pass: durable should-fire 8 > 6; no
  control-durable query lost; durable FP unchanged at 0/8. Shipped in this branch to
  `skills/code-standards/SKILL.md` (description = `descriptions.json:v2`, 146 -> 237 chars).
- v1 was authored pre-run but never executed (the owner stop landed first; v2 satisfied the
  adoption rule alone, so the <=2-variant cap goes unspent). 0 timeouts across 96 probes.

## L2 — body effect (5 evals x {bare, with} x 3 reps; E3 dropped saturated in prescreen)

**KEEP, strong, judge-robust — the strongest body effect measured on canonical record:**

| judge | mean delta (frac-met) | 95% CI | verdict |
|---|---|---|---|
| grok (headline, cross-family) | +0.438 | [+0.186, +0.690] | KEEP (strong) |
| claude (divergence) | +0.389 | [+0.119, +0.659] | KEEP (strong) |

- No verdict flip; expectation-level agreement 0.976 (168 cells; grok stricter on 3, claude on 1).
- Arm means (grok): bare 0.409 frac-met (all-met 6.7%) vs with 0.847 (all-met 46.7%); the with
  arm's worst rep (0.5) beats the bare mean.
- Per-eval deltas (grok): E1 +0.78, E4 +0.60, E5 +0.53, E6 +0.17, E2 +0.11 — positive on all 5.
- The 13-Jul +0.49 lead is canonically CONFIRMED (+0.44 grok / +0.39 claude), and this resolves
  #224 Stage 1's code-standards `d_new` secondary judge-fragility: under the current harness the
  body effect is KEEP under BOTH judge families.

Together the two layers close #214's diagnosis: the skill's body value is large and real, and
the durable-fire gap that forfeited part of it is fixed by the adopted description.

## Costs (pre-registered band $9-20, ceiling $40 — ADR 0073)

Generation: grid $7.40 (30 cells) + prescreen $1.45 + pilot $0.64. Judges: claude $2.65 real,
grok $1.37 notional. Total ~$13.5 — inside the band; ceiling untouched. 0 judge errors.

## Reproduce

```bash
python3 grid.py --prescreen && python3 grid.py --pilot   # gates, already recorded in metadata.json
python3 grid.py                                          # 30 cells -> outputs/   (resumable)
python3 run_trigger.py --variant control                 # trigger-results/control.json (append-only)
python3 run_trigger.py --variant v2
python3 grade.py                                         # graded/cells-{grok,claude}.jsonl (resumable)
python3 aggregate.py                                     # -> results.jsonl + the tables above
```
