---
id: 0097
title: "Rename the bench plugin last, atomically, historical evidence excluded; skill-measure after skill-assay collided"
status: accepted
summary: "Rename now (cost only rises with installs), LAST, live surfaces only. skill-assay was chosen; the execution-time check found it taken, so the pre-decided fallback skill-measure shipped. GLOBAL_TELLS and the marketplace renames map are mandatory members."
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
The collision costs discoverability permanently; execution is one bounded mechanical pass. The
real risk is a PARTIAL rename, so the decision is mostly a completeness spec.

## Assumptions
- [verified] no functional collision today (installs address name@marketplace; GitHub/npm are
  separate namespaces) — the harm is discoverability, which is why this sequences last.
- [verified] the installed Claude Code exceeds the renames-field floor (checked live this
  session).
- [checkable] **WEAKEST:** `renames` has never been exercised in THIS marketplace — owner:
  owner at merge review; result: pending — named signal: the owner's own install migrates at
  the next session start after the rename lands.
- [verified] `skill-assay` was NOT collision-free at execution: npm `skillassay` (16-Aug-2026, an
  agent-context analyzer) — the REOPEN-IF fired; `skill-measure` (npm, PyPI, GitHub free) ships.

## Rejected alternatives
- Stay `skill-bench` — the collision is permanent; the product's pitch is credibility.
- `displayName` only — renames the label, not the thing; recorded as the FALLBACK if the
  acceptance gate proves the rename unsafe.
- `skill-eval` (owner's first proposal), `evaluating-skills` — both heavily collided.
- Rename before the claim fixes — forces hand-written name-correctness on every edit.
- Name-only rename — manufactures the GLOBAL_TELLS under-coverage defect.

## Revisit triggers
- The owner's install does not migrate -> stop; fall back to `displayName`.
- `grep` finds `skill-bench` live outside `benchmarks/` post-gate -> half-rename; fix before
  any further work.
- Real adoption arrives before execution -> re-price the call.

## Act (12-Oct-2026)
- Shipped as `skill-measure`. GLOBAL_TELLS keeps the old name as a leak pattern. The
  `skill-bench` path shim is retired: the plugin left this repo (ADR 0102).
- `SKILL_BENCH_*` env vars keep their names: not a decision-5 member, and renaming them would
  silently drop an adopter's settings.
