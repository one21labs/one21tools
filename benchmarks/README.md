# benchmarks/

Dated dirs are append-only measurement records — never edit or "retrofit" one (ADR 0026; a
re-run either REPRODUCES the committed harness as-is or is a NEW measurement in a new dated dir).

**Scaffold a new benchmark from the harness lib, not by copying the latest dated dir** (ADR 0041):
import `bench_io`/`verdict`/`hermetic_driver` and read the deny-list from
`skill-bench/scripts/lib` (the harness moved into the `skill-bench` plugin per ADR 0055; usage:
that dir's `README.md`); follow the ADR 0023/0026 artifact formats. A copied dir carries
whatever stale conventions it had at its date. (Frozen dated dirs still reference their original
`../lib` paths — append-only records, not re-run.)
