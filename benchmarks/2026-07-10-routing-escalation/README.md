# Routing-escalation benchmark — 2026-07-10 (issue #109)

Does routing — haiku attempts the task once, a checker ships or escalates, on escalate sonnet
redoes the WHOLE task (no coaching) — reach sonnet-solo quality at materially lower cost?
Pre-registered per ADR 0024; methodology: ADR 0019 (eval-clustered), ADR 0023 (hermetic executor),
ADR 0025 (fraction-met, prosecutor min), ADR 0027 (directional bar at small n). The full
pre-registration, including the adoption bar and the checker-fidelity ground truth, is
`metadata.json` — committed before any checker call.

## Why this is cheap: composition over the #41 substrate

`benchmarks/2026-07-10-tiered-execution-fullgrid/`'s haiku-solo and sonnet-solo gradient cells
(8 evals x 3 reps, blind-graded, real per-cell envelope costs) ARE the two halves of the routing
arm. Routing has no coaching — an escalated task is redone from the original request alone — so
`routing(eval, rep) = haiku(eval, rep) if SHIP else sonnet(eval, rep)` is an exact simulation,
not an approximation. The only new spend is the checker calls: 24 haiku cells x 2 model variants,
hermetic `claude -p` (same ADR 0023 pattern, env, and deny list as the substrate's `harness.py`).

## Checker variants (the experiment's real question)

#41 measured its sonnet validator at 25% false-accept — under routing every false-accept ships a
haiku-floor artifact, so checker fidelity is the pre-registered primary secondary metric.

| Variant | Checker | Cost |
|---|---|---|
| `sonnet-judge` | sonnet, sees request + deliverable only (no rubric) | per call |
| `haiku-judge` | same prompt, haiku | per call |
| `mechanized` | SHIP iff ALL of the eval's mechanized structural checks pass (`benchmarks/lib/mechanized_checks.py` via the fullgrid's `graded/mechanized.csv`) | $0 |

`mechanized` caveat: those checks were authored from the eval expectations, so it models
hand-written task-type lint checks — an upper bound for rubric-informed checklists, not a
rubric-free judge (`metadata.json:design.checker_variants`).

**False-accept ground truth (pre-registered):** a SHIP is false iff that cell's haiku frac-met <
(the eval's sonnet-solo mean frac-met − 0.05) — i.e. shipping loses more than the non-inferiority
margin vs escalating. Rate over all 24 cells is the comparable to #41's 6/24; rate among accepts
is also reported.

## Adoption bar (pre-registered, per variant)

ADOPT routing(variant) iff ALL of:
1. `mean_delta(routing − sonnet-solo) > −0.05` frac-met (point estimate, clustered over 8 evals;
   95% CI reported, not gating — ADR 0027 rationale at n=8)
2. median per-cell cost ratio vs sonnet-solo `<= 0.6`
3. false-accept rate over all 24 cells `<= 0.15`

Cheapest clearing variant wins; if none clears, DO NOT ADOPT — recorded either way (ADR 0024).

## Reproduce

```bash
python compose_test.py                                # decision-logic tests
python prep_checker_inputs.py                         # 24 haiku gradient cells -> checker_inputs.json

# Checker calls, inside WSL Debian (hermetic config + empty cwd), one invocation per model variant:
wsl -d Debian -- python3 /mnt/c/Users/ajmcc/projects/one21tools/benchmarks/2026-07-10-routing-escalation/checker_harness.py --variant sonnet-judge
wsl -d Debian -- python3 /mnt/c/Users/ajmcc/projects/one21tools/benchmarks/2026-07-10-routing-escalation/checker_harness.py --variant haiku-judge
# copy \\wsl.localhost\Debian\home\<user>\routing-run\checkers\*.json -> checkers/
#      \\wsl.localhost\Debian\home\<user>\routing-run\*.checker-summary.json -> .

python compose.py                                     # results.jsonl + ADOPT/DO-NOT-ADOPT verdict
```

## Result (2026-07-10) — DO NOT ADOPT

All three variants fail the pre-registered bar; per-cell and per-variant numbers live in
`results.jsonl` (verdict rows), raw checker records in `checkers/`.

| Variant | delta vs sonnet-solo | E (escalation) | false-accept | median cost ratio | outcome |
|---|---|---|---|---|---|
| sonnet-judge | −0.044 | 0.62 | 5/24 (21%) | 1.68 | fails cost + fidelity |
| haiku-judge | −0.058 | 0.54 | 6/24 (25%) | 1.42 | fails all three |
| mechanized | −0.010 | 0.79 | 2/24 (8%) | 1.24 | fails cost |

Two findings worth the spend: (1) #41's validator false-accept **replicates** for model judges
under routing semantics (21–25% vs #41's 25%); (2) the fidelity threat is **solvable** — the
deterministic checklist checker hits 8% false-accept and holds quality at −0.010 (CI lower bound
−0.047 clears the −0.05 margin even at n=8). But routing fails on **cost, structurally**: only
6/24 haiku cells are legitimately shippable here, so a faithful checker escalates ~3/4 of cells
and routing pays for haiku + checker + sonnet on most of them — total cost 1.04–1.33× sonnet-solo
against a ≤0.6× gate. On a battery where the cheap model rarely suffices, no checker can make
routing cheap. Verdict ADR: 0036.

## Limitations (pre-registered)

- n=8 clustered evals — the same graded gradient subset and directional-bar rationale as ADR 0035.
- The gradient battery was selected for tasks where haiku loses to sonnet — exactly the population
  a checker must escalate; a production mix with more haiku-parity tasks would mechanically favor
  routing on cost. The verdict binds this battery only.
- Aggregate half-arm outcomes were public in issue #109 before this pre-registration; per-cell
  grades were not consulted when authoring the checker prompts.
