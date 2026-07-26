---
id: 0063
title: "skill-bench completion set: ratify 0055, skill-bench owns its method references, bundle #191 1-3, defer paid runs"
status: accepted
tier: lite
summary: "Four calls completing #170: (1) flip ADR 0055 proposed->accepted, amended; (2) method references move INTO skill-bench (the measurement product owns its method — standalone install); (3) bundle #191 items 1-3 + item-4 checklist half, split the cross-plugin verifier edit + item 5; (4) defer paid M5/M6 to issues, #150 keeps its own PR, but the zero-spend /plugin install round-trip rides this PR. Also completes M3, ships templates, refreshes README, cuts the lib husk."
---

# 0063 — skill-bench completion set (#170)

- Date: 2026-07-14
- Decision: (1) flip ADR 0055 proposed->accepted, amended — items 2-3 shipped as decided, item 4 partial, item 1's reference clause INVERTED (refs stay in building-skills). (2) method references move INTO `skill-bench/skills/bench/references/` — a lone install otherwise dangles. (3) bundle #191 items 1-3 + item-4's checklist half (own commits); split the cross-plugin verifier-agent edit + item 5 to a follow-up issue. (4) defer paid M5/M6 to issues, #150/ADR 0050 keeps its own PR; the zero-spend `/plugin install` round-trip rides THIS PR. Also: complete M3, ship templates, refresh README, cut the benchmarks/lib husk.
- Why: owner directive + ADR 0056 (cohesive over one-concern) drive one packaged PR; split lines are revert boundaries, not concern counts.
- Rejected: keep the method references in building-skills — a lone install dangles its methodology. Split ALL of #191 — only the cross-plugin edit needs its own boundary. Bundle #150 here — different revert boundary.
- Reopen-if: an adopter needs authoring guidance from a lone skill-bench install -> revisit the split line. `/plugin install` fails in Testing -> 0055 M6 blocked.
- Enforced: `skill-bench/README.md`; ADR 0055 (as amended) and ADR 0050 govern the split PRs.
