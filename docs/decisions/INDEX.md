# ADR index + shared register

The catalog of accepted ADRs and the shared unverifiable-assumption register. The immutable rules +
template live in the plugin template (see `README.md`). Add a new ADR's row here.

Decision validity (`Status`) lives in each ADR file, not this table. Ship-state in `Ships` is a
derived mirror (strike the `→ release` token when its release ships); docs-only ADRs have no release.

| ID | Decision | Ships |
|----|----------|-------|
| [0001](0001-pdca-workflow-extraction-scope.md) | pdca-workflow extraction scope: generic framework in; domain layer + runnable metrics engine + standalone review-system.md out | docs-only |

### Open unverifiable assumptions (shared register)

A shared market/usage fact lives once here; each dependent ADR references it, so one signal reopens
all of them.

| Assumption | Affects | Resolve with |
|------------|---------|--------------|
| A second consumer (a non-LTconfig project adopting the plugin) needs no runnable metrics engine — the language-neutral `metrics-engine.md` spec suffices | 0001 | a real second consumer's request, or its absence after the plugin is used elsewhere |
