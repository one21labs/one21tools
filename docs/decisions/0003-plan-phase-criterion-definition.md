---
id: 0003
title: "Plan-phase criterion-minting: a required, falsifiability-gated step"
status: accepted
summary: "Make minting the per-decision criterion explicit + gated — adr-lint flags an ADR with no falsifiable criterion as UNFALSIFIABLE (reusing existing tags, no new field); name the assumption hit-rate as the emergent quality signal."
---

# 0003 — Plan-phase criterion-minting

- Date: 2026-06-28
- Owner: PM
- Panel: 3 advisors (process-rigor / muda-YAGNI / poka-yoke lenses) + a web-enabled lead-verifier,
  then `verifier` + `red-team` — dogfooded `/decide`. No standing product panel (this repo ships the framework).
- Context: the earlier "no computable metric" frame mislocated the gap. PDCA's Check is BY DEFINITION
  comparison against a target set in Plan, so the success criterion is an OUTPUT of Plan, not a missing
  precondition. The plugin is already an unnamed per-decision criterion lifecycle — Plan mints (an
  ADR's `[checkable]` assumptions + revisit triggers ARE the falsifiable criteria), Check tests them
  (verifier + red-team), Act resolves them (/retrospect). The only gap: minting was implicit/optional —
  an ADR could ship with no falsifiable criterion and nothing flagged it (`adr-lint.mjs:38` checked
  frontmatter/ids/version/cites/budget only). Caveat: a criterion is a per-decision falsifiable
  prediction, NOT a global score to optimize — calibration != decision quality, proxies invite Goodhart [verified, 2404.13503].

## Decision
Make Plan-phase criterion-minting REQUIRED + falsifiability-gated, reusing the existing tag vocabulary
(no new field). `adr-lint` now flags an ADR with no `- [checkable]`/`- [checkable-doc]`/`- [contradiction]`
bullet AND no `- [unverifiable]` paired with a REOPEN-IF as **UNFALSIFIABLE**. It gates PRESENCE (shape);
the PM + gate judge SUBSTANCE (whether a stated criterion is genuinely falsifiable). The corpus-wide
**assumption hit-rate** (resolved `[checkable]` `## Act` outcomes, verified vs refuted) is named as the
emergent, bottom-up quality signal — a read-out, not a target; computed via `metrics-engine.md`, no new home.

## Justification
Closes the lifecycle's one gap at the lowest cost: one executable guard reusing the tags + its tests,
zero new machinery. Failing only the genuinely-empty case keeps a legitimate all-`[unverifiable]`
market-fact ADR (which carries REOPEN-IF) passing — neutralizing the false-positive/Goodhart objection.
Load-bearing, already settled: check trust = INDEPENDENCE (fresh instance + adversarial role), not
vendor-diversity [verified]; the metric is a HIT-RATE, not a Brier score (needs outcomes; n far too small) [verified];
the PM anchor is for ACCOUNTABILITY, not error-immunity (humans are fooled by obfuscated arguments too) [verified].

## Assumptions
- [verified] the guard is new — `lint()` in `pdca-workflow/scripts/adr-lint.mjs` had no criterion check; the guard + 6 cases now ship green (`node --test`, 19/19).
- [checkable] the gate passes the live corpus (0001/0002 + this ADR carry `[checkable]` bullets) and fires only on a criterion-less ADR — verify: `node pdca-workflow/scripts/adr-lint.mjs docs/decisions`.
- [checkable] presence-only: a prose mention of "[checkable]" is not a bullet (line-anchored regex) — covered by a test.
- [unverifiable] consumers act on the flag once they wire adr-lint into CI (this repo runs it by-hand pre-merge; no CI gate exists) — REOPEN-IF a consumer reports the flag ignored.

## Rejected alternatives
- Hard-fail every all-`[unverifiable]` ADR — false-positives on legit market-fact calls; invites fake `[checkable]` (Goodhart). Fail only the zero-criterion case.
- A new required template field / `UNFALSIFIABLE` tag — a second mirror of the existing tag discipline (muda); reuse `[checkable]`/`[unverifiable]`.
- Do nothing, rely on template prose — leaves the silent-skip unguarded; poka-yoke prefers prevent>detect.
- AutoLibra rubric-induction (2505.02820, real + sound) — out-of-scope auto-induction machinery; defer until minting proves hard at scale.
- Build a hit-rate/Brier computation now — `metrics-engine.md` already owns computation; a second home is muda.
- Already-satisfied, recorded so they are not re-added: Bucinca commit-before-verdict (CSCW 2021) is the Plan->Check step order; ExpeL/A-MEM reconcile-not-append (2308.10144 / 2502.12110) is /retrospect step 7; CAI (2212.08073) is precedent for operationalizing principles, NOT proof that "anchors required."

## Revisit triggers
- An ADR is legitimately criterion-less yet correct -> the fail-condition is wrong; reopen it.
- A /retrospect sample shows ADRs gaming the gate with hollow `[checkable]` bullets -> add a substance check or move the judgment fully to the gate.
- A consumer wires adr-lint into CI and the UNFALSIFIABLE flag misfires -> tune the regex.
