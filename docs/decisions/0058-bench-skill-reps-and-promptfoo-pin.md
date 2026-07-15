---
id: 0058
title: "/bench skill: default 3 reps per task x arm; pin the promptfoo version"
status: accepted
tier: lite
summary: "Two harness-hygiene fixes from an owner best-practices review: (1) bench_skill.py gains --reps (default 3) — it ran one generation per task x arm and emitted KEEP/CUT language a single pass cannot support; (2) the promptfoo substrate pins an exact parser-validated version instead of a moving head (pin's one home: substrate.py:PromptfooSubstrate.PIN). Bump rule: re-validate the output parser, then move the PIN constant."
---

# 0058 — /bench reps default + promptfoo pin

- Decision: (1) `bench_skill.py --reps N`, default 3, rep-tagged cells (`id:arm:rN`) into the
  existing clustered stats; `--reps 1` stays for smoke runs; the cost estimate scales by reps.
  (2) `PromptfooSubstrate.PIN` (that constant is the version's one home) replaces the
  moving-head fetch; `$SKILL_BENCH_PROMPTFOO_BIN` still overrides. Owner-direct.
- Why: single-pass with/without deltas cannot separate reliably-good from lucky — the repo's own
  grids rep 3x with clustered CIs (ADR 0019) while the exported tool (skill-bench, extracted
  per ADR 0055) did not; and an unpinned
  substrate silently changes under a pre-registration (the parser is validated per pinned line).
- Enforced: decision-logic tests (rep-bid uniqueness; pin-no-latest) run in required CI.
