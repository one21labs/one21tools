# benchmarks/

Dated dirs are append-only measurement records — never edit or "retrofit" one (ADR 0026; a
re-run either REPRODUCES the committed harness as-is or is a NEW measurement in a new dated dir).

**Scaffold a new benchmark from `lib/`, not by copying the latest dated dir** (ADR 0041):
import `bench_io`/`verdict`/`hermetic_driver` from `benchmarks/lib`; read the tool deny-list
from `lib/deny_tools.txt` (python: `hermetic_driver.CLAUDE_DENY_TOOLS`; bash:
`mapfile -t DENY < lib/deny_tools.txt`); follow ADR 0023/0026 artifact formats
(CSV/TSV/minified JSONL, sampled raw + one `raw.tar.gz`, `sample_rule` in metadata). A copied
dir carries whatever stale conventions it had at its date.
