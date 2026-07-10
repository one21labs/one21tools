---
id: 0033
title: "Vendor the trigger runner as a first-party instrument (detection seam + 4 fixes)"
status: proposed
summary: "Vendor skill-creator's run_eval.py with an extracted pure detection seam + 4 fixes (3 stream patches + timeout-as-null), guard the seam with a fixture test, pin a clean CLAUDE_CONFIG_DIR + SERIAL execution. Method -> new reference description-ablation.md (matched-load A/B; absolute rates never reportable). Scopes ADR 0013's 'No owned harness' to the paired-benchmark harness (now false: benchmarks/lib/ owned)."
---

# 0033 — Vendor the trigger runner as a first-party instrument

- Date: 2026-07-09
- Owner: PM
- Panel: lean-process-engineer + benchmark-operator (converged on vendor+upstream); red-team + live runs folded below.
- Context: description-ablation is recurring (issue #30 folds it into the ADR 0024 loop); its runner is skill-creator's `run_eval.py` + 3 LOCAL patches living only as a diff (`benchmarks/2026-07-07-toolkit-grid/trigger-kit/runner-patches.diff`). Unpatched, the stream loop hard-fails on the first non-Skill/Read tool call and closes detection at `message_stop`, miscounting (diff lines 12-33). Live runs found two more hazards: `--num-workers N>1` collapses rates toward 1/N (concurrent workers share the project root); a timed-out query is scored a False. Own the runner, or re-apply a diff to a moving upstream that can fuzzy-apply into a silent miscount?

## Decision
1. **Vendor with an extracted detection seam + 4 fixes.** Copy to `skills/building-skills/scripts/run_eval.py`; EXTRACT the stream-detection into a pure function (no such seam upstream) so it is testable. Fixes: the 3 stream patches PLUS **timeout-as-null** — a timeout records null, EXCLUDED from the rate, never a False. Header pins PROVENANCE (upstream repo + clone date + the 3 patches + extraction + timeout fix); sync is MANUAL, not a mechanical re-diff. Linux/WSL-only.
2. **Guard the seam with a fixture test** (`run_eval_test.py`): synthetic stream events assert each branch (planted-name block -> fired; unrelated tool then Skill -> fired; non-match at `content_block_stop` then later match -> keep-watch then fired; no trigger -> not-fired; timeout -> null). The Never-rule targets process-gates not instruments, so it doesn't literally bind — but the detection IS the count, so the test is warranted and poka-yokes drift.
3. **Pin config-dir + serial.** The wrapper MUST set `CLAUDE_CONFIG_DIR` to an empty dir (a live run had WSL's dev-skills plugin shadow the variant, zeroing all 64 cells) AND run `--num-workers 1`.
4. **Method home = new reference `description-ablation.md`** (measurement sibling to section-ablation.md, per ADR 0031). MANDATES: `--num-workers 1`, `--timeout 240`, equal-load pairing (control+variant same serial protocol/machine, no concurrent load), timeout-as-null. RESTATES the current-truth competitive-field caveat (SSoT; FINDINGS.md stays a cited dated snapshot); states **absolute rates are NEVER reportable** — only matched-protocol A/B deltas.
5. **File the 3 patches upstream — DEFERRED**, blocked on owner approval to post externally (no-external-actions-without-approval). Track via an issue (ADR 0021).

## Justification
Stands on drift-pinning + recurring-use + the already-owned harness + keeping four hard-won fixes as in-repo, tested, version-controlled knowledge — NOT a permission benefit. Clone+patch-per-run carries the SAME staleness PLUS fuzzy-apply corruption of a correctness diff. LOW cost/risk; the seam + test are the only new machinery.

## Assumptions
- [checkable] `run_eval.py` was absent pre-work — TEST: `find . -name run_eval.py` empty. verified.
- [checkable] empirical-evals.md is 11,160 chars — 840 under REFERENCE_MAX_CHARS=12,000 (validate.py:32), so the ~1,800-char method does NOT fit; a new reference is required. verified.
- [contradiction] ADR 0013's "No owned harness" is now globally FALSE — `benchmarks/lib/` is owned + this ADR vendors the runner. FIX IN THIS PR (rationalize-in-place, intrinsic to this concern — not a second one): scope "No owned harness" to the PAIRED-BENCHMARK harness (paired execution stays delegated); the trigger runner is a different, now-owned harness.
- [checkable] the fixture test covers all 4 fixes incl. timeout-as-null on the seam — owner: gates; result: pending (authored at build).
- [unverifiable] SECONDARY: vendoring may also convert a sometimes-hard-denied action into an allowlistable asset — but the FINDINGS-era deny did NOT recur this session (ran via `wsl bash`), so it is a possible bonus, not load-bearing. REOPEN-IF the deny recurs and blocks the loop.

## Rejected alternatives
- Windows-portable rewrite — gold-plating: sole consumer is WSL.
- Method into empirical-evals.md (saturated) or evaluation-patterns.md (wrong altitude — authoring, not measurement).
- (Clone+patch-per-run, no-test, absolute-rate reporting — rejected under Red-team B2/B3/B4.)

## Red-team (all ACCEPT; MUST-3 justified)
B1 permission benefit unproven -> demoted to secondary [unverifiable]. B2 no upstream test seam -> extract a pure detection fn (in tree), pin provenance, sync=manual. B3 load-sensitivity -> protocol mandates serial+timeout+equal-load+timeout-as-null+no absolute rates. B4 mirror-muda -> alt is worse; added un-vendor triggers. MUST-3 one-concern PR for the 0013 edit -> JUSTIFIED: the scope-correction is this decision's own boundary (rationalize-in-place), not a separate concern. MUST-5 -> restate the caveat in description-ablation.md; FINDINGS.md cited as dated evidence.

## Revisit triggers
- Upstream `run_eval.py` diverges enough to miss a fix -> manual re-diff, re-vendor.
- Upstream fixes the 3 stream bugs -> re-diff, consider un-vendoring.
- skill-creator's runner becomes installable/bundled WITH these fixes -> un-vendor, restore delegation.
- A second, non-WSL consumer appears -> reopen portability.
- Owner approves the upstream filing -> post the patches, close it.
