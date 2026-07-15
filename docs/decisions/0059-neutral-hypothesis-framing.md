---
id: 0059
title: "Neutral hypothesis framing: experiments state falsifiable claims, never primed conclusions"
status: accepted
tier: lite
summary: "Owner-direct: every pre-registration, experiment issue, and eval title states a falsifiable hypothesis neutrally — kill conditions up front, motivation labeled grounding (never evidence), a null an equally valid outcome, titles posing the question and never the answer. Agents read issue/pre-reg text during runs, so advocacy wording is a contamination channel. Shipped homes: /bench Guardrails (full rule) and /decide step 7 (pointer) — installed consumers inherit it."
---

# 0059 — neutral hypothesis framing for experiments

- Decision: the rule above, homed where it executes: `skill-bench/skills/bench/SKILL.md`
  Guardrails (full statement) and `pdca-workflow/skills/decide/SKILL.md` step 7 (pointer).
  #185/#186 rewritten 2026-07-13 as the template (operationalized by ADR 0061). Owner-direct.
- Why: two channels. (1) Human: an outcome-titled issue invites proving-at-any-cost, the
  opposite of ADR 0024's loop. (2) Mechanical: agents read issue and pre-registration text
  in-context; advocacy primes generators and graders, and the harness cannot strip it
  because it arrives as instructions.
- Enforced: prose in the two shipped skills (wording is a judgment a linter cannot grade);
  `contamination.py` sweeps the greppable residue.
