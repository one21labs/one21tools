# benchmarks/

Dated dirs are append-only measurement records — never edit or "retrofit" one (ADR 0041; a
re-run either REPRODUCES the committed harness as-is or is a NEW measurement in a new dated dir).

**Landing a run's results retires the prep-era text in the SAME PR** (ADR 0070): a PR that adds
`results.jsonl` to a dir whose README still says "no run executed" / PREP ONLY must update that
language before merge — never ship results beside contradicting pre-registration boilerplate
(the append-only rule freezes a dir at MERGE, not at authoring; both 10-Jul violations needed
appended corrections, issue #215).

**Scaffold a new benchmark from `skill-bench/templates/`, not by copying the latest dated dir**
(ADR 0041): copy `grid.py`/`blind_cells.py`/`grade.workflow.js` and adapt the ADAPT blocks;
import `bench_io`/`verdict`/`hermetic_driver` and read the deny-list from
`skill-bench/scripts/lib` (the harness moved into the `skill-bench` plugin per ADR 0055; usage:
that dir's `README.md`); follow the ADR 0023/0026 artifact formats. A copied dir carries
whatever stale conventions it had at its date.

**Path preservation when shared code moves** (ADR 0089): keep the paths a frozen dir cites
resolvable — an executable dependency gets a forwarding shim, a doc-only cite a pointer stub or
appended correction; the frozen line itself is never edited.
`scripts/check-relocated-paths.mjs` gates the BACKTICKED cites only; un-backticked and relative
forms are deliberate residue (that script's SCOPE header). So a dir predating the gate can still
name a moved path in plain text — the pre-extraction benchmarks/lib README, now
`skill-bench/scripts/lib/README.md`, is cited that way in several dated dirs. Those lines are
frozen records, not a backlog: append a correction if one is worth writing, never edit them.
