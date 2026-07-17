# benchmarks/

Dated dirs are append-only measurement records — never edit or "retrofit" one (ADR 0026; a
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
whatever stale conventions it had at its date. (Frozen dated dirs still reference their original
`../lib` paths — append-only records, not re-run.)
