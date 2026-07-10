---
id: 0034
title: "sections-benchmark never-task redesign: de-confound + pre-registered falsifiable reads"
status: accepted
summary: "Fix the 4 never-task cells (issue #72) as de-confounding under PRE-REGISTERED numeric reads: n1 gets an output-only criterion (a crashed script alone FAILS); n2 names pytest+coverage.py; n4 KEEPS its pressure cell live (0/0 is valid signal; empirical-evals.md:51 requires a pressure case) AND adds elicitable n4b; n3 escalates once to 6 reps then a clean null. Ceiling (both arms >=0.8) = rewrite; intermediate + delta~0 = clean null counting toward ADR 0024's cut budget."
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
6. **Full tier** (live triggers + pending re-run).

## Justification
Each fix targets a diagnosed CONFOUND (crash, ambiguity, noise) or preserves honest signal (the veto null), keeping difficulty where it discriminates — the 0/0 rule and ADR 0024 D3. The pre-registered reads make ceiling vs. null a mechanical call decided BEFORE the numbers, so no result is manufactured post-hoc.

## Assumptions
- [checkable] the diagnosis's discrimination check re-graded OLD (old-prompt) without-arm transcripts under NEW criteria — this does NOT prove the NEW prompts avoid ceiling. TEST before trusting the redesign: fresh without-arm runs under the new n2/n4b prompts must land below 0.8 AND below the with-arm. owner: benchmark-operator; result: pending (the re-run).
- [checkable] n1's SIGPIPE arises from the model's OWN `yes|head` construction (arguably a model error, not a pure harness artifact) — the output-only criterion makes the attribution MOOT: a crashed script fails regardless of cause. owner: verifier; result: pending (inspect a with-arm transcript).
- [unverifiable] a live pressure cell + n4b measures more than either alone — REOPEN-IF the pressure cell stays flat 0/0 across 3 valid iterations with no verdict movement; then retire it to a recorded finding.

## Rejected alternatives
- Retire n4's pressure cell (my prior call) — survivorship bias + violates the >=1-pressure-case floor (empirical-evals.md:51); the 0/0 is signal.
- n1 mechanics-forgiveness carve-out — grades intent; the output-only criterion is objective.
- Rewrite n3 harder — it discriminates; noise is a reps problem (ADR 0019); blind harder-rewrites regressed 6 cells.
- Read a both-arms-high wash as "section adds no value" — that is ceiling, fixed by rewrite (item 5).

## Red-team (all ACCEPT)
B1 unfalsifiable reads -> pre-registered ceiling (>=0.8) + clean-null band + cut-license (item 5). B2+B3 survivorship/lost pressure -> REVERSED: keep pressure-n4 live + add n4b. B4 n1 grades intent -> output-only criterion; SIGPIPE attribution moot. B5 n2 confound -> direction-independent de-confounding; re-run yields a countable null. B6 n3 no stop rule -> one escalation to 6 reps then clean null; relabeled a boundary-straddling tie.

## Revisit triggers
- Fresh without-arm runs under the new prompts land >=0.8 -> ceiling confirmed; soften the ask, rewrite.
- The Never section's cells reach 3 valid clean-null iterations (ADR 0024) -> license a cut/deprioritize decision.
- A proposal to strengthen the section against explicit minimalism -> the live pressure cell measures it.
