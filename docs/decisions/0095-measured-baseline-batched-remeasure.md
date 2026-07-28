---
id: 0095
title: "Measured means measured-at-baseline; out-of-loop edits accrue to a batched G>=8 re-measure"
status: accepted
summary: "The measurement promise is owed to the CLAIM, not to the edit: a verdict means measured at its dated baseline, out-of-loop edits ship freely tracked by git alone (no ledger artifact), and the debt is paid by a batched hermetic re-measure at G>=8 that MUST run before any new or upgraded measured claim about that skill ships."
---

# 0095 — measured-at-baseline + batched re-measure

- Date: 2026-07-28
- Owner: PM
- Panel: plugin-adopter, process-economist, lean-process-engineer; session-operator skipped —
  execution realism is not the binding constraint here. All three converged on scoping rather
  than re-measuring; they split on the debt's home. Economist dissent (track debt as one standing
  issue) rejected: a second home for what git already records. Post-decision gates — verifier
  (BLOCK, fixed in place), red-team, grok-4.5 foreign lane (ADR 0093: this record is
  measurement doctrine), late session-operator pass — surviving findings folded in.
- Context: README.md:3-4 states the paired-eval promise UNCONDITIONALLY — nothing scopes it to
  the dated baselines the evidence actually covers (quoted nowhere here: this record rewords that
  line, so a copy would be stale on landing). ADR 0024 decision 2(d) requires a re-measure only
  per improvement-loop iteration, and no gate fires on an unmeasured edit (checked against
  `.github/workflows/gates.yml`). Measured 28-Jul-2026: 8 distinct commits since 2026-07-19
  edited measured-skill CONTENT (SKILL.md or `references/`) with no re-measure; the newest
  benchmark dir is dated 2026-07-18. Per skill: code-standards 0, building-skills 4,
  optimizing-context 2, engineering-principles 6. The promise sat above its enforcement.
  Owner directive 28-Jul-2026: "everything must improve this repo for the adopter."

## Decision
1. A "measured" claim means measured AT the dated baseline dir the README measured-state block
   cites — never at HEAD. **The obligation is owed to the CLAIM, not to the edit:** an
   out-of-loop edit owes nothing at the moment it ships.
2. Out-of-loop edits (owner findings, retrospect adoptions, doc fixes) ship without a re-measure.
   Their accumulation is READ, not tracked: `git log --since=<baseline-date> -- <source>/<name>`
   IS the ledger — the WHOLE skill dir under its plugin source (`skills/`, `pdca-workflow/`,
   `skill-bench/`); scripts and evals count, they are the gate and the instrument. No ledger
   file, no standing issue — nothing that can rot. Git is the audit surface, not an immutable
   one (this history was rewritten 27-Jul): the rewrite-proof anchor is CONTENT — a paired run
   commits `treatments/<skill>*.txt`, and a byte-compare against the live body survives any
   rewrite.
3. Debt is paid by a BATCHED hermetic re-measure at G>=8 evals. Forcing function: a PR that
   adds, upgrades, or restates-after-drift a measured claim for skill S — on ANY shipped claim
   surface: the README block, pdca-workflow/README.md Measured, skill-bench/README.md — must
   cite a benchmark dir that measured the CONTENT the PR ships (committed treatment
   byte-matches the live body; a dir DATE is not provenance and misfires on same-PR
   revise-and-re-measure, e.g. da76cbc). The PR body pastes that check's output — evidence in
   the diff, because merges here are self-merges in minutes (measured: 15/15, several <10 min).
   Baselines are per-CLAIM, not per-skill.
4. A batch below 8 post-prescreen evals is DIAGNOSTIC ONLY: it may retire a claim or mark it
   UNDERPOWERED in the claim line; it never discharges debt for a KEEP or an upgrade — only
   G>=8 does. A batch that authors new evals records the eval-set diff vs the cited baseline
   and, while #317 is open, the skill-expectation overlap number; a claim whose instrument
   changed never renders as a sharpening trend.
5. README lands as implementation of this record (wording free, no cap on that file): the
   headline claim carries its true scope, and the measured block stays free of hand-maintained
   counters — a dated baseline never rots, an edit count does.
6. ADR 0024 decision 2(d) governs the IN-loop case and is unchanged by this record, which
   decides only the out-of-loop case 0024 left silent. In/out-of-loop is a PROCESS fact, never
   a label: an edit is in-loop iff it ships with the benchmark dir that measured it; every
   other edit under the skill's dir is out-of-loop debt by path.

## Justification
Per-edit re-measurement at the batteries this repo actually runs is underpowered: MDE 0.24-0.37
at G=6 across the observed cluster spread (t-arithmetic, reproduced via `benchstats.mde80`;
sim: issue #303) against July deltas of +0.009..+0.27. Re-measuring now buys likely-INCONCLUSIVE verdicts for ~$63 and changes no
decision. Scoping the promise DELETES the overclaim instead of building machinery to service it —
the subtractive half of the trade, and the half the adopter actually feels: a claim they can
trust beats a thermometer they never see.

## Assumptions
- [checkable] **WEAKEST — everything rides on it:** 8 discriminating evals per skill are
  reachable at all. If they are not, decision 4's cap makes this record indistinguishable from
  "never re-measure". owner: the first batched re-measure; result: pending — named signal: that
  batch's post-prescreen G, recorded in its benchmark dir.
- [verified] all four measured skills' batteries hold exactly 6 eval cases today — read from each
  `skills/<name>/evals/evals.json`. G>=8 therefore requires AUTHORING evals; it is not a
  sampling choice available at batch time.
- [verified] no gate fires on an unmeasured edit — `.github/workflows/gates.yml` carries no
  re-measure step; the promise is enforced by nothing today.
- [checkable] git history alone reconstructs each skill's unmeasured-edit set (no edit channel
  bypasses git) — owner: PR review; result: verified — `git log --since=2026-07-19 -- skills/`
  returns 9 commits: the 8 content commits plus 8d698bc's pointer stubs.
- [unverifiable] the simulation's MDE generalizes to these skills' true effect sizes —
  REOPEN-IF a G>=8 batch measures a single-edit effect >=0.35, which a per-edit design would
  have caught; per-edit re-measurement then regains its value.

## Rejected alternatives
- Re-measure all measured skills now at G=4-6 — ~$63 for four likely-INCONCLUSIVE verdicts
  against underpowered denominators; and code-standards has ZERO content edits since its
  baseline, so one of the four would measure nothing at all.
- Revert the unmeasured edits — reintroduces known-false claims that later commits fixed
  (40cd021), destroying shipped adopter value to satisfy literalism.
- A standing debt-ledger, as a file or as one open issue — a second home for what git already
  records, and the same un-gated-tracker shape this repo deleted once for gating nothing and
  never being run (README.md:73-74, issue #311).
- A mechanical CI gate on unmeasured edits — premature: the failure it would catch has not yet
  occurred (no measured claim has shipped on a stale baseline). Revisit trigger 1 escalates to
  it on the first real instance, so the gate is bought with evidence, not anticipation.

## Revisit triggers
- A measured claim ships whose cited dir did not measure the shipped content -> the PR-body
  forcing function failed; escalate to a mechanical gate (predicate exists:
  treatment-vs-live-body byte-compare).
- The first batch cannot reach 8 discriminating evals -> decide explicitly: invest in eval
  authoring, or retire that skill's measured claim from the README.
- ADR 0024's improvement loop is run on a skill whose out-of-loop debt is unpaid -> fold the
  batch into that loop's iteration 1 rather than paying for two measurements.
- `keep_verdict` renders a bare KEEP below 8 clusters -> add the engine floor
  (INCONCLUSIVE/UNDERPOWERED below the floor), not more prose.
