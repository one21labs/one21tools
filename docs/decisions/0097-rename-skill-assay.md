---
id: 0097
title: "skill-assay is the name of record; the rename executes last, atomically, historical evidence excluded"
status: accepted
summary: "Adopt skill-assay (two independent naming lanes converged; zero collisions found) and execute the rename — cost rises monotonically with installs and is at its global minimum now. Sequenced LAST, after the claim fixes and doc scoping. GLOBAL_TELLS and the marketplace renames map are mandatory members: missing either turns a rename into a silent measurement defect or a plugin-not-found."
---

# 0097 — rename to skill-assay

- Date: 2026-07-29
- Owner: PM
- Panel: none spawned; two adversarial evaluations both said defer-execution-pending-an-ADR —
  this IS that ADR; their name-only-rename warning is decision 5.
- Context: the plugin name collides with the GitHub org `skill-bench` (same niche, ships a
  marketplace action) and `skillbench` on npm + PyPI. Two independent naming lanes converged on
  `skill-assay`; alternates `skill-measure`, `skill-lift`.

## Decision
1. `skill-assay` is the name of record. The naming question is closed; a fourth lane is waste.
2. Execute — not gated on adoption. Cost rises monotonically with installs; today is the global
   minimum. The live alternative was never/now, not now/later.
3. Sequence LAST: claims (ADR 0096) -> doc scoping (ADR 0098) -> rename. A mechanical global
   substitution must run over final text.
4. Live surfaces only; `benchmarks/**` is EXCLUDED verbatim — dated dirs record what ran;
   rewriting them falsifies evidence and breaks ADR 0095's byte-compare anchor.
5. Mandatory members (missing any one = defect, not rename): (a) `contamination.py:29-30`
   GLOBAL_TELLS carries the literal name as a leak pattern — missing it leaves a detector
   under-covering; (b) marketplace gains `"renames": {"skill-bench": "skill-assay"}` — without
   it an existing install errors plugin-not-found; (c) every ADR file token into `skill-bench/`
   repoints or adr-lint fails; (d) install strings, the `skill-bench:bench` namespace,
   `gates.yml`, `check-relocated-paths` (a rename IS a relocation, ADR 0089).
6. Acceptance gate: `grep -rn skill-bench` outside `benchmarks/` returns only the renames map's
   old key; adr-lint exit 0; validate.py passes; owner runs `/plugin marketplace update` THEN
   `/reload-plugins`.
7. The owner's merge review of the rename PR is the confirmation point — this record decides
   name and shape; it is not consent to execute.

## Justification
The collision costs discoverability permanently and compounds; execution costs one bounded
mechanical pass, char-neutral in every budgeted file. The real risk is a PARTIAL rename, so the
decision is mostly a completeness spec.

## Assumptions
- [verified] no functional collision today (installs address name@marketplace; GitHub/npm are
  separate namespaces) — the harm is discoverability, which is why this sequences last.
- [verified] the installed Claude Code exceeds the renames-field floor (checked live this
  session); `skill-assay` and `SKILL_ASSAY` are char-identical to what they replace, so
  budgeted files survive.
- [checkable] **WEAKEST:** `renames` has never been exercised in THIS marketplace — owner:
  owner at merge review; result: pending — named signal: the owner's own install migrates at
  the next session start after the rename lands.
- [unverifiable] `skill-assay` is still collision-free at execution — REOPEN-IF the re-run
  check finds one -> fall to `skill-measure`; no new naming lane.

## Rejected alternatives
- Stay `skill-bench` — the collision is permanent; the product's pitch is credibility.
- `displayName` only — renames the label, not the thing; recorded as the FALLBACK if the
  acceptance gate proves the rename unsafe.
- `skill-eval` (owner's first proposal) — the most-collided candidate found.
  `evaluating-skills` — gerund-correct, HIGH collision.
- Rename before the claim fixes — forces hand-written name-correctness on every edit.
- Name-only rename — manufactures the GLOBAL_TELLS under-coverage defect.

## Revisit triggers
- The owner's install does not migrate -> stop; fall back to `displayName`.
- `grep` finds `skill-bench` live outside `benchmarks/` post-gate -> half-rename; fix before
  any further work.
- Real adoption arrives before execution -> re-price the call.
