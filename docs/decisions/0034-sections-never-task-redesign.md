---
id: 0034
title: "sections-benchmark never-task redesign: de-confound + pre-registered falsifiable reads"
status: accepted
tier: lite
summary: "De-confound the never-task cells (issue #72) under pre-registered reads: n1 output-only criterion, n2 names pytest+coverage.py, n4 keeps its pressure cell + adds elicitable n4b, n3 one escalation then stop. Re-run outcome: all five cells floored 0/0 in both arms — the floor is environmental (honest models refuse to claim unexecuted verification), so the never cells are unmeasurable in a text-only harness; a measurement limit, not a section verdict."
---

# 0034 — sections-benchmark never-task redesign

- Date: 2026-07-09
- Decision: de-confound the four never-task cells (issue #72). n1: pass requires an executable test OR a worked walkthrough with line-counts on both sides of 500. n2: name pytest+coverage.py (an unnamed stack stalled both arms). n3: one escalation to 6 reps, then stop. n4: KEEP the pressure cell (0/0 is honest signal) and ADD elicitable n4b (drop "nothing else"). Reads pre-registered: both arms >=0.8 = ceiling (rewrite); both intermediate, delta ~0 = clean null, toward ADR 0024's cut budget (3 valid iterations).
- Why: each fix targets a diagnosed confound or preserves honest signal; pre-registered reads make ceiling-vs-null mechanical, decided before the numbers.
- Result: re-run floored 0.0/0.0 on all five cells, both arms, incl. n4b. The harness forbids execution; honest models refuse to claim verification they didn't run, shipping artifacts + walkthroughs instead. The floor is ENVIRONMENTAL — a measurement limit, not a section verdict.
- Rejected: retire the n4 pressure cell — 0/0 is signal, not survivorship bias. n1 mechanics-forgiveness — grades intent. Rewrite n3 harder — noise is a reps problem.
- Reopen-if: a harness variant that can EXECUTE model-produced checks becomes available -> re-run the never cells.
- Enforced: `skill-bench/skills/bench/references/empirical-evals.md`.
