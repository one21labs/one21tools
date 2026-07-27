---
id: 0041
title: "Propagate benchmark conventions by deriving from lib, not copying stale dirs"
status: accepted
summary: "Fix the stale-benchmark-copy vector at its root: new harnesses DERIVE shared helpers (bench_io, verdict) from skill-bench/scripts/lib and read its one dual-language deny-list home (deny_tools.txt). Add a top-level benchmarks/README scaffold note. Reject a new benchmark gate and reject rewriting pre-ADR-0026 dated dirs (append-only; the frozen literal is the record)."
---

# 0041 — propagate benchmark conventions by deriving from lib, not copying stale dirs

- Date: 2026-07-10

## Decision
1. **Poka-yoke — new harnesses DERIVE shared helpers from the harness lib, not redefine them.**
   Delete duplicated helper mirrors; import `bench_io`/`verdict` from `skill-bench/scripts/lib`,
   also the ONE dual-language deny-list home (`deny_tools.txt`, read by python and bash).
2. **Durable scaffold note at the copy source.** Add a top-level `benchmarks/README.md`: scaffold
   from lib, follow ADR 0026 artifact formats, do NOT blind-copy the latest dated dir — one home
   the next scaffolder sees regardless of which dir is newest.
3. **REJECT a new check-benchmark.mjs gate now** — disproportionate at this benchmark rate, and
   derive-from-lib removes the code-duplication cause (prevent > detect). Revisit trigger below.
4. **REJECT rewriting pre-ADR-0026 dated dirs.** A dated benchmark is an append-only measurement
   record, and git blobs persist so a rewrite reclaims no footprint. The fix is forward-looking.

## Justification
Derive-from-lib is the doctrinal poka-yoke (delete the mirror, derive don't duplicate): it fixes
the duplication at one home so the next copy inherits the correction, beating a detection gate on
cost AND on prevent-over-detect. The frozen harnesses keep their stale inline deny-list because a
re-run is either a REPRODUCTION (correct to keep) or a NEW measurement (a new dated dir
scaffolding from lib) — the frozen literal is the record, not a bug.

## Assumptions
- [verified] deny-list was triplicated as literals with no lib import (read 2026-07-10); PR #123
  then extended the lib home, leaving the dated-dir copies divergent (stays as-is per item 4).
- [checkable] after the fix, no benchmark harness redefines the tool list literally — grep finds
  the list at exactly one lib home. — owner: verifier at implementation.
- [unverifiable] copy-the-previous-dir stays the scaffolding habit (the vector) — REOPEN-IF a
  stale-copy miss recurs post-fix (>1/week), making a gate cheaper than derive-discipline.

## Rejected alternatives
- bench-init scaffold tool — upfront machinery at this benchmark rate; the copy habit persists.
- check-benchmark.mjs gate — detection over prevention; the one recurrence is cause-removed.
- Retrofit pre-0026 dated dirs — immutability + git persistence make it churn, no footprint gain.
- Per-dir "do not copy" mark on the oldest dir — the copy source is the LATEST dir, which moves.
- Python-constant deny-list imported by bash — bash can't import a Python list.

## Revisit triggers
- A stale-copy miss recurs after derive-from-lib ships -> the gate earns its cost; build
  check-benchmark.mjs (with tests).
- A new benchmark needs a helper the lib lacks -> extend the lib, don't re-copy.

## Act (post-ship — 2026-07-10)
- [outcome] verified: `deny_tools.txt` is the single live home (frozen dated copies stay per item 4, PR #127).
- [outcome] still-open: the bash `mapfile` read of that home. PR #127 shipped no bash consumer and none exists today (`mapfile` appears only in comments/prose, no `.sh` file) — the 2026-07-26 outcome audit corrected this row's original, unsupported claim.
