---
id: 0051
title: "One decision-set per PR, gated by cite-graph connectivity"
status: accepted
summary: "The PR unit for ADRs is the decision-set: multiple new ADRs ship together iff their cites form one connected (undirected) graph — enforced by adr-lint --new-adrs in a PR-only CI step. Dangling-cite stays strict; revise-in-place unchanged."
---

# 0051 — one decision-set per PR

- Date: 2026-07-12
- Owner: PM
- Panel: advisor evidence + options argued on issue #171; PM accepted. The pdca panel primitives were unavailable in the authoring session (plugin not loaded).
- Context: issue #154. The template's one-ADR-per-PR rule collides with the dangling-cite guard (adr-lint.md check 4): ADRs that cite each other cannot ship in separate PRs, because whichever merges first cites a record that is not on disk. PR #151 shipped ADR 0047, ADR 0048, ADR 0049, ADR 0050 as one four-record set — a violation in letter that the lint and corpus absorbed cleanly, and the deliberation was the better for reviewing its trade-offs together.

## Decision
1. **The PR unit is the decision-set, not the ADR.** A PR introduces one new ADR, or several whose cites entangle them into a single deliberation. The template rule (adr-template.md) is reworded in the same change.
2. **Set membership = undirected connectivity.** The new ADRs in a change must form ONE connected component of the cite graph, where an edge exists when either record cites the other. Full mutual citation is NOT required: in the precedent set, 0048 and 0047 never cite each other — the four connect only through 0050's one-way cites — so a mutual-only bar would flag the very shape that motivated this decision.
3. **The dangling-cite guard stays strict.** It is the mechanized protection for corpus integrity, and it is what makes the set boundary real: the records that must ship together are exactly those that guard would fail apart.
4. **Mechanized, fail-open.** `adr-lint --new-adrs=<added files>` runs the connectivity check; a PR-only `gates.yml` step feeds it the diff-added ADR files. Flag absent, empty, or naming a single new ADR = check skipped, so push-to-main runs, consumer checkouts, and local runs are untouched.
5. **Revise-in-place is unchanged** — a still-unmerged ADR gets edited, never accompanied by a sibling written to overrule it; that half of the old rule was never in question.

## Justification
Prose to machinery: recent process failures lived in prose rules while the mechanized guards held, and this converts the batching rule into a tested gate. Revert atomicity points the same way — rolling back one member of an entangled set would strand cites in the survivors, so the set IS the atomic unit the old rule assumed the single ADR was. At current merge cadence, serializing an entangled set also multiplies in-flight branches (the #164 merge-skew class) for zero review benefit.

## Assumptions
- [checkable] The precedent shape passes and unrelated batching fails: the real 0047-0050 corpus files clear `decisionSetProblems`, while two new ADRs sharing no cite are flagged — owner: adr-lint.test.mjs decision-logic cases; result: verified in the shipping change.
- [checkable] Fail-open is real: an absent/empty `--new-adrs` and a singleton list report nothing — owner: adr-lint.test.mjs; result: verified.
- [unverifiable] Connectivity is strict enough in practice — a token cite could bridge genuinely unrelated decisions — REOPEN-IF a merged PR is found to have joined unrelated ADRs via a cite that exists only to satisfy the gate; tighten to a mutual edge per member.

## Rejected alternatives
- **Relax the dangling-cite guard for cross-PR forward cites** — trades a working mechanized guard for coordination prose; a forward cite whose PR never merges is permanent corpus damage.
- **Require full mutual citation** — fails the precedent set (decision 2) and would push authors to write artificial cites to satisfy the gate.
- **Discourage mutual citation** — severs real coupling future readers need.
- **Delete the rule** — unbounded batching of unrelated decisions degrades review granularity; the set boundary keeps the rule's value.

## Revisit triggers
- A gamed set merges (a bridge cite with no semantic content) -> tighten the bar per the assumption above.
- The CI diff wiring proves brittle (shallow-fetch or rename misses) -> move new-file detection into the lint itself or adopt a merge queue (the open #164 finding-2 question).
