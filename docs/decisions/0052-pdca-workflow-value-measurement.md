---
id: 0052
title: "PDCA-workflow value measurement: both instruments, shared plumbing pilot, cost-gate as hard stop"
status: accepted
summary: "Execute #172's two value instruments as pre-registered (retrospect recall + /decide three-arm outcome), with three plan fixes: a shared plumbing pilot precedes EITHER grid (I1 is NOT plumbing-free); the I2 cost-pilot is a HARD stop via a benchmarks/lib cost-gate; blind.py homes in benchmarks/lib. Committed pre-regs before spend are the checkable artifact."
---

# 0052 — PDCA-workflow value measurement plan

- Date: 2026-07-12
- Owner: PM
- Panel: process-economist, session-operator, lean-process-engineer (plugin-adopter skipped — internal measurement scope; the consumer angle is only #172's mandated claim-accuracy update).
- Context: the flagship plugin is the least-evidenced artifact — ADR 0049 declined trigger-testing for lack of a without-arm; #172 measures VALUE instead (without-arm: bare Claude + cost-matched deliberation) and mandates `/decide` before spend. Three plan errors surfaced.

## Decision
1. **Scope: execute BOTH as pre-registered** — I1 retrospect recall, I2 `/decide` three-arm outcome. No trim. Keep arm B (cost-matched unstructured, issue:16): the without-arm closing "measures spend, not structure"; cutting it unfalsifies C>B.
2. **Sequencing: one shared plumbing pilot precedes EITHER grid.** The plan flags plumbing only for I2, but `deny_tools.txt:1-19` denies every tool and `hermetic_driver.py:9-10` pins a no-plugin config, so BOTH arms' C need the carve-out + plugin load (I1: Read/Grep/Glob/Bash, `retrospect.md:5`; I2: subagent spawn + panel, `decide/SKILL.md:11-12`). Run **1 retrospect + 1 decide cell** proving the driver can invoke a skill+agent at all. Order: **plumbing pilot -> I1 grid -> I2 cost-pilot -> I2 grid** (I1 first among grids: cheap, objective, validates grading, issue:9-10).
3. **Spend control: the I2 cost-pilot is a HARD stop.** 0042:13 records 216 cells run past a ~5-cell decidable gate (~90% saveable); 0042:38 says the fix is "a gate script". Discharge it: the cost-pilot (2-3 arm-C cells) writes measured per-cell cost into the pre-reg; a minimal **benchmarks/lib cost-gate** EXITS NONZERO if projected grid cost > the **$40** I2 ceiling (pilot capped ~$6). Over cap -> halt, record, fresh `/decide`. Ships with a unittest (CLAUDE.md Never rule). **Gate outcomes (pilot records in the dated dirs):** I1's $15 gate fired ($0.375/cell -> $18.02/48) — fresh `/decide` set ceiling **$30**; I2's $40 gate fired ($9.07/cell -> $242-653/72) — owner funded the full grid, ceiling **$300**. Both designs (substrates/scenarios, reps, bars) untouched: only spend parameters moved, pre-grid.
4. **blind.py normalization homes in `benchmarks/lib`**, imported by both instruments — NOT a 10th copy of the layer already in 9 dated dirs (matches `hermetic_driver.py` post-#110). The 9 copies stay frozen (append-only dated dirs: ADR 0041, `empirical-evals.md:159`).
5. **Checkable artifact:** both pre-regs (scenarios, expectations, rubric, arms, C>B bar, n, cost ceiling) committed BEFORE any grid spend; precedence readable off git order + per-call timestamps (`hermetic_driver.py:16-18`). Verdicts via `lib/verdict.py`, eval-clustered CIs (0019), `met_final=min(grader,prosecutor)` (0025), blinding validated by a guess-the-arm audit (`2026-07-08-grading-bias-audit/` precedent); weak/strong CI language pre-committed (n=3 wide).

## Justification
Both earn spend: I1 is low single-digit dollars, objective, de-risks I2's pipeline; I2 is the flagship's only outcome-level evidence. Prior art predicts C~B on compute-matched verifiable tasks but the open-ended-judgment regime is unpublished — so C>B is a genuine falsifiable bar, and C~B REPLICATES prior art (routed to its own `/decide`, issue:19), not a failure. The three fixes are each cheapest: shared pilot over double plumbing; one gate script (prevent > re-detect); one lib home over copy #10.

## Assumptions
- **[checkable] WEAKEST — the whole grid rides on it: arm C's plumbing is FEASIBLE and its per-cell cost is knowable only after the pilot.** No benchmark has run a live skill+agent stack through the all-tools-denied driver (`hermetic_driver.py:31-32`: subagent/Task denied *because* a nested session leaks the parent task list). TEST (verifier): the pilot log shows the deny-list conflict HIT and RESOLVED (isolation preserved), not just tokens priced; projected grid lands under $40. Result: verified 2026-07-12 (`2026-07-12-pdca-plumbing-pilot/`).
- [checkable] `deny_tools.txt:1-19` denies all 19 tools; `hermetic_driver.py:9-10` pins a no-plugin config; `blind.py` sits in 9 dated dirs with no lib home — result: verified (gate reproduced, 2026-07-12).
- [checkable-doc] no accepted ADR contradicts: 0049 declined TRIGGER-testing (different question), 0006 tiers the retrospect agent (I1 records it, issue:8), 0023 owns recorded-null, 0041 owns append-only — result: verified.
- [unverifiable] author-written scenarios represent consumer decisions — partly mitigated by the synthetic set (issue:23). REOPEN-IF a consumer's `/decide` outcome diverges from the corpus.

## Rejected alternatives
- I1 as plumbing-free warm-up (the plan's sequencing premise) — false per Decision 2.
- Cost-pilot as advisory gate — 0042:13 shows that pattern overspent once.
- Retro-consolidate the 9 blind.py copies — edits append-only dated dirs (ADR 0041); separate concern.

## Revisit triggers
- Plumbing pilot: arm C cannot load the panel/skill or leaks isolation -> halt; reopen whether a non-hermetic directional run is worth recording (0023:37).
- Cost-pilot projects > $40 -> gate halts; fresh `/decide` on trimming cells/arms.
- Guess-the-arm audit shows blinding leaks -> re-decide grading (schema-rewrite blinding is unvalidated in prior art).
- C~B on the grid -> route to its own `/decide` (buys tokens, not structure); don't silently keep the claim.
