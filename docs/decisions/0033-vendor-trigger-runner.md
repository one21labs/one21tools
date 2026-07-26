---
id: 0033
title: "Vendor the trigger runner as a first-party instrument (detection seam + 4 fixes)"
status: accepted
tier: lite
summary: "Vendor skill-creator's run_eval.py with an extracted pure detection seam + 4 fixes (3 stream patches + timeout-as-null), guard the seam with a fixture test, pin a clean CLAUDE_CONFIG_DIR + serial execution. Method home: description-ablation.md — absolute rates never reportable, only matched-protocol A/B deltas. Scopes ADR 0013's 'no owned harness' to the paired-benchmark harness."
---

# 0033 — vendor the trigger runner as a first-party instrument

- Decision: copy skill-creator's `run_eval.py` in-repo (now `skill-bench/scripts/run_eval.py`),
  extracting stream-detection into a pure, testable function. Fixes: 3 stream patches (the
  unpatched loop hard-fails on non-Skill/Read tool calls and closes detection too early) plus
  **timeout-as-null** (a timed-out query records null, excluded from the rate, never scored
  False). Guard the seam with a fixture test (`run_eval_test.py`). Pin `CLAUDE_CONFIG_DIR` to
  an empty dir + `--num-workers 1` (concurrent workers shared project root, zeroing runs).
- Why: drift-pinning + recurring use + an already-owned harness beat clone-and-patch-per-run,
  which carries the same staleness plus fuzzy-apply corruption of a correctness diff.
- Rejected: a Windows-portable rewrite — gold-plating, sole consumer is WSL. Clone+patch-per-run
  with no test and absolute-rate reporting — refuted under red-team review.
- Reopen-if: upstream `run_eval.py` diverges enough to miss a fix -> manual re-diff, re-vendor.
  Upstream fixes the 3 stream bugs, or ships the runner installable-with-fixes -> un-vendor. A
  second non-WSL consumer appears -> reopen portability.
- Enforced: `skill-bench/scripts/run_eval.py` + `run_eval_test.py`; method rules in
  `description-ablation.md` (serial execution, timeout-as-null, no absolute rates).
