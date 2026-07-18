---
id: 0076
title: "Bench cost estimates derive from measured $/cell priors, never guesses"
status: accepted
tier: lite
summary: "Amends ADR 0066's estimate line: the initial notional estimate must derive from the most recent measured $/cell for the same judge/model in prior committed metadata.json cost blocks; with no prior, the 2-cell pilot runs BEFORE any number is recorded. Third instance of a guessed estimate missing by >2x (ADR 0061 17x; PR #219 pilot > ceiling; PR #227 $8 guessed vs $28.23 actual) — 0066's record-the-gap rule catches the miss but nothing stopped the guess. Closes #228."
---

# 0076 — derive cost estimates from measured priors

- Decision: one line added to `skill-bench/skills/bench/references/cost-and-verdict.md` (the
  cost-rule SSoT): initial estimates come from prior committed `metadata.json` actuals for the
  same judge/model; no prior → pilot first, then record. No gate machinery (0066 precedent —
  a mechanical warn stays the named escalation if guessing recurs despite the rule).
- Why: the miss class is thrice-recorded and the fix is a lookup that costs nothing — every
  dated dir already commits its actuals, so the prior always exists after one run.
- Enforced: the cost-and-verdict.md line every pre-registration cites; estimate-vs-actual
  stays checkable per run from the recorded actuals.
