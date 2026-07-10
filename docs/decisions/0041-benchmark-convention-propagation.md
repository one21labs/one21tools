---
id: 0041
title: "Propagate benchmark conventions by deriving from lib, not copying stale dirs"
status: accepted
summary: "Fix the stale-benchmark-copy vector (#87/#101/#108) at its root: new harnesses DERIVE shared helpers (bench_io, verdict) from benchmarks/lib and read one designed dual-language deny-list home (lib/deny_tools.txt, python + bash, PR #123's Task* extension folded in). Add a top-level benchmarks/README scaffold note (copy-the-latest makes a per-dir mark worthless). Reject a new benchmark gate and reject rewriting pre-ADR-0026 dated dirs (append-only; a re-run is reproduction-or-new-dir, so the frozen literal is the record)."
---

# 0041 — Propagate benchmark conventions by deriving from lib, not copying stale dirs

- Date: 2026-07-10
- Owner: PM
- Panel: lean-process-engineer, process-economist, session-operator, plugin-adopter.
- Context: New benchmarks are scaffolded by copying the previous dir; conventions and the shared lib don't propagate. Verified 2026-07-10: the deny-list is triplicated as hand-copied literals — hermetic_driver.py:28 (CLAUDE_DENY_TOOLS), harness.sh:21 (bash array), tiered.py:28 (python list) — none imports the lib, none carries the new Task*/collaboration tools (#108 isolation hole); harnesses ship byte-identical aggregate.py/blind.py/archive_raw.py ignoring benchmarks/lib (#87); the 2026-07-10 scaffold copied pre-ADR-0026 artifact formats from 2026-07-08-skills-hermetic (#101).

## Decision
1. **Poka-yoke — new harnesses DERIVE shared helpers from benchmarks/lib, not redefine them** (#87). Delete the duplicated helper mirrors; import bench_io/verdict from lib. The deny-list gets ONE designed dual-language home — a lib-owned newline-delimited `benchmarks/lib/deny_tools.txt` read by python (`(LIB/'deny_tools.txt').read_text().split()`) and bash (`mapfile -t DENY < "$LIB/deny_tools.txt"`), no jq; PR #123's Task* extension moves into it. Fix the home once; new harnesses read it.
2. **Durable scaffold note at the copy source** (#101): the vector is copy-the-LATEST dated dir, which moves, so a per-dir mark on the oldest dir (2026-07-08) misses it — instead add a top-level `benchmarks/README.md` (does not exist today) reading "scaffold a new benchmark from lib: read deny_tools.txt, import bench_io/verdict, follow ADR 0026 artifact formats; do NOT blind-copy the latest dated dir." One home the next scaffolder sees regardless of which dir is newest; the artifact-format vector (data, not importable) is closed for the next copy because the latest dir (2026-07-10) is already 0026-conformant.
3. **REJECT a new check-benchmark.mjs gate now** — disproportionate at n≈2 dirs/day, carries a Never-rule test burden, and derive-from-lib removes the code-duplication cause (prevent > detect). Keep as a revisit trigger.
4. **REJECT rewriting pre-ADR-0026 dated dirs** (#87 retrofit): they predate 0026 (conformant at creation; 0026 is silent on retrofit), a dated benchmark is an append-only measurement record (empirical-evals.md:159), and git blobs persist so a working-tree rewrite reclaims no footprint. Completed dated runs (incl. 2026-07-10) stay as-is; the fix is forward-looking.

## Justification
Derive-from-lib is the doctrinal poka-yoke (CLAUDE.md — delete the mirror, derive don't duplicate): it fixes #87 and #108 at one home so the next copy inherits the correction, beating a detection gate on cost AND on prevent-over-detect. The top-level scaffold note (not a per-dir mark) is the one home that survives copy-the-latest and covers the un-importable artifact-format class. The eight existing frozen harness.sh files keep their stale inline deny-list: a dated benchmark is an append-only record, and a re-run is either a REPRODUCTION (the original deny-list is exactly what was measured — correct to keep) or a NEW measurement (a new dated dir that scaffolds from lib) — so the frozen literal is the record, not a bug. Rejecting the gate and the dated-dir retrofit avoids gold-plate and churn against immutable records.

## Assumptions
- [verified] deny-list triplicated as literals, no lib import: hermetic_driver.py:28, harness.sh:21, tiered.py:28 — read 2026-07-10; PR #123 then extended the lib home with the Task* tools, leaving the dated-dir copies divergent (append-only, stay as-is per item 4).
- [verified] benchmarks/lib is the intended one home (bench_io.py, verdict.py; "One home instead of copy-pasted", lib/README.md) — read 2026-07-10.
- [verified] append-only immutability of dated records — empirical-evals.md:159; ADR 0026 silent on retrofit — read 2026-07-10.
- [checkable] after the fix, no benchmark harness redefines the tool list literally — grep finds the list at exactly one lib home — owner: verifier at implementation.
- [unverifiable] copy-the-previous-dir stays the scaffolding habit (the vector) — REOPEN-IF a stale-copy miss recurs post-fix (> 1/week), making a gate cheaper than derive-discipline.

## Rejected alternatives
- bench-init scaffold — upfront machinery at n≈2/day (gold-plate); the copy habit persists anyway.
- check-benchmark.mjs gate — detection over prevention; test burden; the one traced recurrence is cause-removed by derive-from-lib.
- Retrofit pre-0026 dated dirs / rewrite the 8 frozen harness deny-lists — immutability + git persistence make it churn with no footprint gain.
- Per-dir "do not copy" mark on the oldest dir — the copy source is the LATEST dir, which moves; the mark orphans. Top-level README instead.
- Python-constant deny-list imported by bash — bash can't import a Python list; `deny_tools.txt` is the language-neutral home.

## Revisit triggers
- A stale-copy miss recurs after derive-from-lib ships → the gate earns its cost; build check-benchmark.mjs (with tests).
- A new benchmark needs a helper the lib lacks → extend the lib, don't re-copy.
