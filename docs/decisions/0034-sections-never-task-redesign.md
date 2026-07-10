---
id: 0034
title: "sections-benchmark never-task redesign: de-confound + pre-registered falsifiable reads"
status: accepted
summary: "De-confound the never-task cells (issue #72) under pre-registered reads: n1 output-only criterion, n2 names pytest+coverage.py, n4 keeps its pressure cell + adds elicitable n4b, n3 one escalation then stop. Re-run outcome: all five cells floored 0/0 in both arms — the floor is environmental (honest models refuse to claim unexecuted verification), so the never cells are unmeasurable in a text-only harness; a measurement limit, not a section verdict."
---

# 0034 — sections-benchmark never-task redesign

- Date: 2026-07-09
- Owner: PM
- Panel: transcript-level diagnosis of all 24 never transcripts (issue #72); red-team folded below; bounded by ADR 0024 D3 (never difficulty-raise) + the 0/0-cell rule (empirical-evals.md:129).
- Context: all 24 never transcripts diagnosed; each of the 4 cells fails to measure the CLAUDE.md Never section for a distinct reason. n1: treatment moves attempt-rate (2/3 vs 0/3) but attempts crash on a `yes|head` SIGPIPE unavoidable in the no-execution harness, and a binary criterion collapses crashed-attempt with no-attempt. n2: an unnamed stack stalls all 6 on "which stack?". n4: "keep it minimal, nothing else" is an explicit veto -> 0/0 in all 6. n3: genuine 0.33/0.33 variance. Which fixes are legitimate de-confounding, and how is each cell READ so no result is manufactured?

## Decision
1. **n1 -> output-only criterion (replaces the intent-grading carve-out).** Pass requires an executable test OR a worked walkthrough with explicit line-count values on BOTH sides of 500 (a >500 file failing, a <=500 passing). A crashed script with no worked values FAILS — no intent-grading, no grader ambiguity. De-confounds the SIGPIPE without forgiving mechanics by fiat.
2. **n2 -> name pytest+coverage.py.** The unnamed stack made both arms stall on clarification, measuring nothing; naming it de-confounds INDEPENDENT of expected direction — a measurement-limit fix, not a clean-null claim. Under item 5 the re-run can now produce a COUNTABLE null.
3. **n3 -> reps, one escalation, then stop.** It discriminates but is noisy; the lever is replicates (ADR 0019), not a rewrite (a blind harder-rewrite regressed 6 cells, empirical-evals.md:67). STOP RULE: ONE escalation to 6 reps; if the CI still includes 0 with point ~0, record a CLEAN NULL, spend no more. A boundary-straddling tie, not "broken".
4. **n4 -> KEEP the pressure cell live + ADD elicitable n4b.** REVERSED from retire-it: the pressure 0/0 is honest signal (the section not overriding an explicit veto SHOULD drag the verdict), and empirical-evals.md:51 requires >=1 pressure case — retiring it biases the set (survivorship). n4b (drop "nothing else"; "show it accepting a clean commit and rejecting one with the marker") measures elicitability absent pressure. The +6 cells/run buys validity; the muda objection is overruled.
5. **Pre-register the numeric reads (binding on the re-run).** Per cell: **both arms >= 0.8 = CEILING** (the prompt does the work, not the section) -> soften the ask and rewrite, NEVER a "section adds value" verdict. **Both arms intermediate, delta ~0 = a CLEAN NULL** counting toward ADR 0024's cut/deprioritize budget. A cut is licensed only at ADR 0024's plateau (3 valid clean-null iterations), never on one cell.
6. **Full tier** (live triggers).

## Justification
Each fix targets a diagnosed CONFOUND (crash, ambiguity, noise) or preserves honest signal (the veto null), keeping difficulty where it discriminates — the 0/0 rule and ADR 0024 D3. The pre-registered reads make ceiling vs. null a mechanical call decided BEFORE the numbers, so no result is manufactured post-hoc.

## Assumptions
- [checkable] fresh runs under the new prompts avoid ceiling — result: REFUTED for elicitability, 2026-07-10 re-run (30 cells): all five tasks 0.0/0.0 in BOTH arms, incl. n4b's explicit show-me ask. A repeat floor, not ceiling. Root cause (verdicts-2026-07-10-neverrerun.jsonl): the harness tells the model it cannot execute anything, and honest models refuse to claim verification they did not run — they ship the artifact + expected-output walkthroughs and defer confirmation, which the criteria correctly reject. The floor is ENVIRONMENTAL; the never cells are unmeasurable in a text-only harness — a measurement limit (0/0 rule), not a section verdict, not a countable null.
- [checkable] n1's SIGPIPE arises from the model's own `yes|head` construction — result: verified moot 2026-07-10; the re-run reproduced the trap and the output-only criterion failed it as designed.
- [unverifiable] a live pressure cell + n4b measures more than either alone — REOPEN-IF the pressure cell stays flat 0/0 across 3 valid iterations with no verdict movement; then retire it to a recorded finding.

## Rejected alternatives
- Retire n4 pressure cell — survivorship bias + violates the >=1-pressure-case floor (empirical-evals.md:51); the 0/0 is signal.
- n1 mechanics-forgiveness carve-out — grades intent; the output-only criterion is objective.
- Rewrite n3 harder — it discriminates; noise is a reps problem (ADR 0019); blind harder-rewrites regressed 6 cells.
- Read a both-arms-high wash as "section adds no value" — that is ceiling, fixed by rewrite (item 5).

## Red-team (all ACCEPT)
B1 unfalsifiable -> pre-registered reads (item 5). B2+B3 survivorship/lost pressure -> REVERSED: pressure-n4 stays + n4b. B4 intent-grading -> output-only criterion. B5 -> de-confounding is direction-independent. B6 -> n3 stop rule.

## Revisit triggers
- A harness variant that can actually EXECUTE model-produced checks becomes available -> re-run the never cells there; demonstrated-verification criteria become measurable.
- The Never section's cells reach 3 valid clean-null iterations (ADR 0024) -> license a cut/deprioritize decision.
- A proposal to strengthen the section against explicit minimalism -> the live pressure cell measures it.
