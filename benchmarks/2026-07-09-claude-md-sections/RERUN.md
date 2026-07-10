# Never-section re-run (issue #72, ADR 0034)

Prep only — no `claude` calls have been made from this prep. This documents the exact steps to
run the 30 cells and fold their verdicts into `results.jsonl` once someone executes them.

## 1. Run the grid (WSL Debian)

```bash
wsl -d Debian -- bash /mnt/c/Users/ajmcc/projects/wt-never/benchmarks/2026-07-09-claude-md-sections/rerun-never.sh
```

Reads `rerun-cells.tsv` (regenerate with `python prep.py && grep '^never' cells.tsv > rerun-cells.tsv`
if not present — both are gitignored, mechanically derived from `tasks.json`) and
`prompts/never.*.txt` (from the same `prep.py` run). Writes 30 files to `rerun-outputs/`:
`never.<task_id>.<arm>.<rep>.txt` for the 5 task ids x {with,without} x {1,2,3}.

## 2. Blind

```bash
python rerun-blind.py
```

Writes `graded/items/<bid>.json` for the 30 new cells (bid = `sha256("rerun." + filename)[:12]` —
a namespace distinct from `blind.py`'s `sha256(filename)[:12]`, so it can never collide with the
original run's bids for n1/n2/n3/n4, which reuse the same task ids under redesigned criteria).
Also writes `graded/arm_map-2026-07-10-neverrerun.tsv` (same 6-column schema as `arm_map.tsv`) and
`graded/bids-2026-07-10-neverrerun.json` (the 30 bids) — the original `graded/arm_map.tsv` and
`graded/bids.json` are untouched.

## 3. Grade (Workflow tool, from the session — not a CLI step)

```
Workflow grade.workflow.js {itemsDir: "graded/items", bids: <contents of graded/bids-2026-07-10-neverrerun.json>} -> returns [{bid,pass,met,total,evidence}, ...]
```

Persist the returned array as **minified JSONL**, one record per line, to:

```
graded/verdicts-2026-07-10-neverrerun.jsonl
```

Do **not** write into `graded/verdicts.jsonl` or `graded/verdicts-2026-07-09-regrade.jsonl` — this
is a new, separate overlay file (append-only convention, ADR 0019).

## 4. Aggregate

```bash
python aggregate.py
```

`aggregate.py` now (issue #72 patch):
- loads `graded/arm_map.tsv` plus any `graded/arm_map-*.tsv` extensions, in sorted-filename order
- loads `graded/verdicts.jsonl` plus any `graded/verdicts-*.jsonl` overlays (broadened from the
  original `verdicts-*-regrade.jsonl`-only glob), in sorted-filename order
- resolves one bid per `(section, task_id, arm, rep)` **slot**, with later-loaded files winning —
  so the 30 new never-rerun rows *supersede* the original never-section rows for n1_ci_gate,
  n2_coverage_threshold, n3_lint_rule, and n4_min_hook slot-for-slot (same task id, redesigned
  prompt/criterion — blending old- and new-criteria pass/fail values in the same cell would corrupt
  the delta), while n4b_min_hook_elicitable simply adds a new slot (no prior counterpart).

Verified: with no `arm_map-*.tsv` / extra `verdicts-*.jsonl` files present, `aggregate.py`'s output
is byte-identical to pre-patch (`results.jsonl` unchanged); a synthetic single-slot override was
confirmed to replace only that one slot's observation, not add to it, and to leave every other
section (conventions/docs/review-panels/shipping) untouched.

## Deviations from the task brief

- **`metadata.json`'s `sample_rule.population` covers only the 120 ALREADY-archived files** (the
  original run, matching `outputs/all.tar.gz` + the current committed sample exactly) — not the 30
  pending never-rerun cells. `eval_verdict.py --check-audit-sample` hardcodes
  `outputs_subdir="outputs"` with no CLI override, and `rerun-outputs/` must stay a directory
  distinct from `outputs/` (n1/n2/n3/n4's rerun filenames are IDENTICAL to their original-run
  filenames — copying them into `outputs/` would silently overwrite the original run's committed
  audit sample). Rather than list files the checker can never find (which the task brief allowed as
  a fallback: "structure population to list only currently-existing files"), the rule was scoped so
  `--check-audit-sample` returns a genuine `[OK]`/exit 0 today, and this file documents why —
  a stronger outcome than "only parses." After the run, verify the 30 `rerun-outputs/*.txt` files
  by hand against the grid in `metadata.json:grid` (5 task ids x 2 arms x 3 reps); there is no
  tooling gap to fill beyond that (an `outputs_subdir` CLI flag would be the generalizable fix, but
  is out of scope for this prep — file an issue if a future benchmark needs a second sampled
  directory audited).
- **`aggregate.py` needed two patches**, not the one the task brief anticipated: (1) read
  `arm_map-*.tsv` extensions (as expected), and (2) broaden the verdicts-overlay glob from
  `verdicts-*-regrade.jsonl` to `verdicts-*.jsonl` so `verdicts-2026-07-10-neverrerun.jsonl` (a
  filename that does not match `*-regrade.jsonl`) is actually picked up. Also added slot-level
  (not just bid-level) supersession — without it, the rerun's fresh bids for n1/n2/n3/n4 would have
  *added* observations to the same cell alongside the original run's stale-criteria bids, silently
  averaging pre- and post-ADR-0034 measurements together. All three changes were verified against
  the live `graded/` data (see "Verified" above).
