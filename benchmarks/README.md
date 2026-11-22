# benchmarks/

Dated dirs are append-only measurement records — never edit or "retrofit" one (ADR 0041; a
re-run either REPRODUCES the committed harness as-is or is a NEW measurement in a new dated dir).
Evidence an ADR cites lands on main as a dated dir — never only on a branch (deletable without
review) or a tag (agents don't fetch tags).

**Landing a run's results retires the prep-era text in the SAME PR** (ADR 0070): a PR that adds
`results.jsonl` to a dir whose README still says "no run executed" / PREP ONLY must update that
language before merge — never ship results beside contradicting pre-registration boilerplate
(the append-only rule freezes a dir at MERGE, not at authoring; both 10-Jul violations needed
appended corrections, issue #215).

**The harness is a separate repo** (ADR 0102): clone
[one21labs/skill-measure](https://github.com/one21labs/skill-measure) and export
`SKILL_MEASURE_ROOT` to it. A frozen dir reproduces exactly by checking out one21tools at the
commit that landed it — the harness was in-tree then. `benchmarks/lib/` shims load from
`SKILL_MEASURE_ROOT` and exit naming this remedy when it is unset.

**Scaffold a new benchmark from the harness's `templates/`, not by copying the latest dated dir**
(ADR 0041): copy `grid.py`/`blind_cells.py`/`grade.workflow.js` and adapt the ADAPT blocks;
import `bench_io`/`verdict`/`hermetic_driver` and read the deny-list from its `scripts/lib`
(usage: that dir's `README.md`); record the harness commit in `metadata.json`; follow the ADR
0023/0026 artifact formats. A copied dir carries whatever stale conventions it had at its date.
No gate checks this; a stale-copy miss recurring is the trigger to build one.

**When shared code moves** (ADR 0089): the frozen line is never edited. A dir that cites a
moved path reproduces at the commit that landed it; no gate checks those paths. Append a
correction if one is worth writing.
