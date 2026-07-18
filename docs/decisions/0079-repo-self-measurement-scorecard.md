---
id: 0079
title: "Repo self-measurement scorecard: north-star as compass, ship a gated hit-rate + a mechanical reference-veracity hook, defer graders + Level-1"
status: accepted
summary: "Operationalize the README goal as a COMPASS (corrections/shipped-work at cost), not a gate — flagged for owner confirmation. Ship NOW: the assumption hit-rate as the first metrics-engine.md implementation (controlled-vocabulary input, fail-loud unparsed, coverage row, PARTIAL verdict) + reference-veracity as a mechanical PR-diff hook. Accept DERIVED/CITED/MEASURED routing as doctrine. Defer every grader-needing rate and Level-1 (design in #236, gated on PR #219)."
---

# 0079 — repo self-measurement scorecard

- Date: 2026-07-18
- Owner: PM
- Panel: lean-process-engineer + process-economist + session-operator (plugin-adopter omitted — repo-local surface). Revised post-gate (verifier B1; red-team BREAK 1-4 / PRESSURE A-C).
- Context: owner wants the README goal measured to prove "better than any alternative" (issue #240). Owner rulings: metrics are GATES not optimization targets; instrument bar = the owner ranking criterion (loop-engineering.md:20-22). Detail lives in the build home `scripts/scorecard.mjs` (+ test); this ADR carries decisions + criteria.

## Decision
**(a) North-star = COMPASS, not a gate — OWNER-CONFIRMATION item (flagged for morning review).** "Corrections per unit shipped work, at cost" is a lagging composite with no direct sensor — gating it means gating its inputs, a day-one mirror. Numerator from committed artifacts, never transcripts (mining one needs an LLM grader — the gaming vector owner flagged). Live proxies = (b)'s two instruments; the direct corrections-per-PR numerator awaits a mechanical defect marker (deferred). Compass demotion relaxes "gates, PERIOD" — an owner-signed override, not a panel call (REOPEN-IF below).

**(b) Ship a gated hit-rate + a mechanical reference-veracity hook; defer/reject the rest.**
- SHIP — **assumption hit-rate**, the repo's FIRST `metrics-engine.md` implementation (`scripts/scorecard.mjs` + decision-logic test). Answers the gate via four guards (detail → build home): a controlled outcome vocabulary `verified|violated|still-open` enforced tonight by a NEW `adr-lint` check + `adr-template.md` line (BREAK 1); unparsed → NOT EVALUATED, excluded from both denominators, never dropped, the 5 untagged corpus lines re-audited tonight; an ADR-age COVERAGE row (full-tier, `Date:` > N days, no `## Act` = uncovered — Act-presence being the ship marker) + a lite-share readout (BREAK 2); a gated AGGREGATE where every deferred instrument prints NOT INSTRUMENTED each run and the verdict reads PARTIAL while any miss-class is uninstrumented (BREAK 3). rate = violated/(verified+violated); FIRE/WATCH fire a /decide, `minSample`-gated, exit-0 — not a CI block, not an optimization target (PRESSURE B). Constants (N≈14d per the ~50-PR/wk cadence; bands ≈0.30) are config.
- SHIP — **reference-veracity** as a MECHANICAL PR-diff hook (BREAK 4): a diff adding an external URL / arXiv-ID to a tracked corpus path (docs/research, docs/decisions) must also touch a `sources/*-reference-audit*` record; own decision-logic test. Prevent-at-write becomes HONEST (the doc-rule at `loop-engineering.md:26-31` was detection-by-reviewer): the hook forces the record to EXIST (syntactic); the fetch-audit's truth stays the manual adversarial step (layered, ADR 0046). It mechanizes because its trigger is syntactic; defect-escape cannot (semantic numerator) — why one ships and one defers (the :44 reconciliation).
- DEFER — each needs a grader or un-minted marker (verified absent): **defect-escape** (no defect/escape label; #215/#216 unlabeled; no revert commits — squash repo), **owner-intervention rate** (no correction-taxonomy in repo; classifying a correction is an LLM call — same self-report failure as the citation "verified" label), **summary-truthfulness spot-audit** (reference-veracity's surface one scope wider — ship the narrower recorded-catch one first).
- REJECT as gates (no recorded miss + gaming surface): **cycle-time**, **cost-per-decision** — readout columns only. REFERENCE, don't re-ship: **estimate-accuracy** (ADR 0076), **verdict-robustness** (Level-2).

**(c) Epistemic routing — ACCEPT DERIVED/CITED/MEASURED as doctrine TEXT, not a classifier.** Homes a short block in `metrics-engine.md` (incl. the "measurement is the WRONG tool" clause — a wide-CI null doesn't override a strong derivation; MEASURE only behavioral/transfer-doubtful/decision-changing claims, each naming its gating decision before spend), ref'd from `/decide` step 1.

**(d) Level-1 vs-alternatives — REJECT build-now, DESIGN-AND-DEFER.** Blocker (issue's own): PR #219 infra-asymmetry — orchestration plugins cannot express under hermetic tool-denied `claude -p`. Derived cost $360-480 (120 cells × $3-4/cell at the measured orchestration profile), ~3-5x the largest committed run ($95.50, `benchmarks/2026-07-12-pdca-decide-outcome/README.md`), before task authoring — fails the recorded-miss bar. Design (arms, blockers, task adoption from SkillsBench/superpowers-evals) records in #236 (ADR 0021); no fresh doc now. Execution gated on #219 resolved AND a battery adopted → 2-cell pilot (ADR 0076) → ceiling.

**Persistent-layer re-audit (issue's open gap: committed facts have no revisit triggers).** DEFER the periodic sweep — the reference-veracity write-time hook is the primary control; a periodic detection sweep is a mirror layered on prevention, built only if prevention leaks.

## Justification
Every shipped item is now grader-free AND mechanically enforced (hit-rate via controlled-vocabulary lint; reference-veracity via a PR-diff hook), clearing "gates, period"; every deferred item needs a grader that IS the catastrophic gaming surface. The BREAK-driven guards are validity preconditions, not gold-plating — they stop the scorecard reading green while misses are dropped or miss-classes uninstrumented.

## Assumptions
- [unverifiable] WEAKEST — the whole (a)/(b) rides on it: hit-rate (decision-premise correctness) + reference-veracity (citation truthfulness) MOVE WITH the real trust gap (owner corrections per shipped PR) while the direct corrections numerator stays deferred. If they don't correlate the scorecard isn't measuring trust; BREAKs 1/2 make the proxy author-steerable, so a LIVE trigger: REOPEN-IF the owner records a correction neither instrument anticipated, OR the coverage row degrades below its band, OR (once shipped) a mechanical defect marker diverges from the proxies.
- [checkable] the hit-rate reconciles to all 17 outcome lines and the keyword miner undercounts misses. owner: verifier. result: VERIFIED — 8 verified / 1 violated / 3 still-open / 5 unparsed (=17); re-audit normalizes the 5 (+4 verified, +1 violated — the #185 FALSIFIED miss at `0061`), so true resolved > 12 and the naive rate understates misses; controlled-vocab + fail-loud are mandatory. B1 cost also corrected: largest run $95.50 (`benchmarks/2026-07-12-pdca-decide-outcome/README.md`); 120 × $3-4 = $360-480 ≈ 3.8-5x.
- [checkable] PR-rate gates are NOT sample-starved. owner: verifier. result: VERIFIED — 143 PRs merged Jun28–Jul18 (`gh pr list --state merged`), ~50/week; the sample worry is per-skill-battery deltas, not repo cadence.
- [checkable-doc] no settled ADR contradicted; lite-exemption gaming already blocked. result: VERIFIED — 0076's "no gate machinery" is the per-run hard-stop, not this read-out; metrics-engine.md:3 fires a /decide on a threshold crossing (a review, not a CI block — PRESSURE B); adr-lint check 6 rejects a lite ADR with a live criterion; 0078 is max, 0079 free.

## Rejected alternatives
- Gate the north-star composite directly — no direct sensor; gates a mirror of its inputs.
- Reference-veracity as a manual doc-rule / a human `defect-escape` label — suppressible self-reports; mechanize (hook) or defer (no syntactic marker), never ship as an unenforced "gate".

## Revisit triggers
- Owner rules the north-star must be a hard gate → re-open (a); the flagged PRESSURE-A confirmation item.
- Owner records a correction neither shipped instrument anticipated, OR the coverage row drops below its band → re-open the WEAKEST proxy-faithfulness assumption (live, not deferred-gated).
- A mechanical defect/correction marker ships → build defect-escape as a second instrument. A correction taxonomy + adversarial audit lands (#236) → owner-intervention rate graduates to gate.
- The reference-veracity hook is bypassed or a citation miss recurs → escalate the hook (audit-quality check, 0066/0076). A contaminated fact the hook did NOT catch → build the periodic re-audit (prevention leaked).
- PR #219 resolved AND a task battery adopted → run the Level-1 2-cell pilot, then set a ceiling.
- Hit-rate refute-rate, still-open, or uncovered share crosses its band → fire a /decide (premise failure / uncheckable-claim drift / coverage decay).
