---
id: 0013
title: "building-skills eval guidance: delegate empirical eval, build no harness"
status: accepted
summary: "Trim-vs-extend the building-skills eval story. Call: DELEGATE, build nothing. Keep the self-contained PROSE, but relabel the stale eval JSON template as illustrative + gate the pointer with schema-differs + stricter-house-rule caveats. Build NO harness — zero eval artifacts exist in-repo (a gate guards air). Capture two zero-machinery wins as authoring discipline (an A/B-split delta; fresh grader on the harness path), soften the evals-first MANDATE to manual guidance, and route the rest UPSTREAM."
---

# 0013 — building-skills eval guidance: delegate, build no harness

- Date: 2026-07-04
- Owner: PM
- Panel: opposing counsel — 2 sonnet advisors (steelman trim+delegate; steelman extend), never primed — plus 1 neutral sonnet harness-design lens, unprimed. Verifier PASS-with-notes + red-team (5 breaks, all accepted + folded) ran the gate.
- Context: building-skills forked the OLD skill-creator; Core Principles duplicate it near-verbatim (SKILL.md:16-108) and evaluation-patterns.md:16-27's eval JSON is the OLD schema. The NEW skill-creator ships a Python eval harness but is NOT in this marketplace nor bundled in Claude Code — a consumer cannot reach it. Trim + point at skill-creator, or extend with a better harness?

## Decision
**DELEGATE the empirical layer; build no runnable harness. One concern, one PR.**
1. **Keep the PROSE, relabel the stale format.** Core Principles (SKILL.md:16-108) are a legitimate vendored fork, not a drifting mirror (0011 B8) — keep. BUT evaluation-patterns.md:16-27's JSON is the OLD shape; the NEW evals.json differs on every key (upstream schemas.md:11-35) -> relabel it ILLUSTRATIVE, not skill-creator's wire format.
2. **Gated pointer (cite-or-silence), two caveats.** In evaluation-patterns.md (the reference, not the near-cap body), APPEND a CONDITIONAL pointer ("if skill-creator is installed, run its harness; else the steps above suffice") + the agentskills.io/skill-creation/evaluating-skills URL. Caveats so it can't mislead: (a) skill-creator's evals.json schema differs from the shape above; (b) validate.py stays authoritative here — skill-creator's own description fails its trigger-start rule (validate.py:155-159). Never bare.
3. **Build NO harness — neither tier.** Not the spawn/grade/iterate loop + viewer + `claude -p` optimizer (non-deterministic, un-CI-able, re-forks an upstream that already superseded itself — gold-plating). AND not Advisor 2/3's "narrow" schema-validator/gate.py: zero eval artifacts (evals.json/benchmark.json/grading.json) exist anywhere in-repo [verified], so a gate over them guards an empty road — premature machinery is muda. validate.py stays the sole deterministic, tested, required-CI gate (0012).
4. **Two zero-machinery wins + fix the unfollowable mandate** (evaluation-patterns.md / SKILL.md, prevent > detect):
   - (a) extend the Claude A/B split (SKILL.md:117-119) to eval AUTHORSHIP — write assertions as fresh Claude B, not the author (a delta on A/B, not a new rule).
   - (b) on the HARNESS path only, grade in a fresh/independent model (robustness; inert on the manual fallback, which has no grader step).
   - (c) soften SKILL.md:113-115 + checklist:165 from a MANDATORY "Build Evaluations First" gate to explicitly-manual authoring guidance — empirical execution is delegated. Keep the body <=6,000.

## Justification (answers "how to improve the harness — and where")
Advisor 3's ranked fixes, by home:
- **LOCAL now (zero machinery):** author-separation (an A/B delta) + fresh grader on the harness path — the poka-yoke form of two upstream weaknesses (contamination; grader-model coupling).
- **UPSTREAM (a skill-creator issue/PR, not built here):** independent grader `--model` (grader.md exposes none vs run_eval.py:268 — a robustness gap, not a proven bug), CI `--fail-under` + regression-vs-history, better stats, seed/model metadata, multi-skill triggering, drop-HTML. Not ours to fork.
- **NOT worth it:** dollar-cost accounting; the runnable loop / viewer / optimizer.
DELEGATE: LOW / LOW, self-sufficiency preserved. EXTEND: value unrealized until an eval-producing workflow exists — which it does not.

## Assumptions
- [verified] No eval artifacts in-repo — grep for evals.json/benchmark.json/grading.json returns nothing; a gate over them guards air.
- [verified] shipped sizes (validate.py normalization): SKILL.md body 5,489/6,000 (5,341 pre-edit); evaluation-patterns.md 3,489/12,000 — the SKILL.md change is the softening only.
- [checkable] the pointer ships conditional-with-fallback, never bare, carrying both caveats; the agentskills.io URL resolves live. — owner: verifier (diff + WebFetch).
- **[unverifiable] WEAKEST: no consumer needs an OWNED harness — the empty eval-artifact road reads as no-demand, NOT as an unfollowable mandate now cemented.** Softening the mandate (4c) makes the discipline followable manually, removing that reading. REOPEN-IF a consumer authors evals.json in-repo -> then Advisor 2's tested schema-validator is worth building (a local gate, not the loop).

## Rejected alternatives
- Cut Core Principles to point at skill-creator (the "above" proposal) — consumer can't reach it; recreates 0011 B2's dangling cite.
- Rewrite the template to the CURRENT evals.json schema — reintroduces an upstream-tracking mirror that drifts on the next schema change; illustrative-only is the poka-yoke.
- Build the narrow schema-validator/gate.py now — no eval artifacts to gate; speculative muda, deferred behind the REOPEN-IF.

## Revisit triggers
- A consumer (or this repo) authors evals.json in-repo -> build Advisor 2's tested schema-validator as a local deterministic gate.
- skill-creator ships in this marketplace or bundles in Claude Code -> the pointer drops its conditional fallback + caveats.
