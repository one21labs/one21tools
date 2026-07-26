---
id: 0002
title: "Generalize the plugin for any project; ADR = Authoritative Decision Record; /roadmap-review -> /decide"
status: accepted
tier: lite
summary: "ADRs ARE the plan-of-record (roadmap optional); strip stack/UI/process leaks; rename the expansion + the decision-panel skill."
---

# 0002 — generalize the framework for any project + naming

- Decision: ADRs ARE the plan-of-record (a roadmap/changelog is an optional human-readable projection, never a self-graded skip) — build-order is dependency order among unshipped accepted ADRs, ship-state is derived from a dated `## Act`. ADR now stands for "Authoritative Decision Record" (was "Architecture" — too narrow); the `/roadmap-review` skill renamed `/decide` (it is the decision panel, not a roadmap review). Stripped structural leaks the plugin had baked in: UI idioms, a guaranteed `ROADMAP.md`, a versioned-manifest assumption — each generalized to "any stack/product-shape/process."
- Why: one defect class — a generic tool hardcoding a stack/UI/artifact/process assumption it already generalizes elsewhere; the always-present ADR corpus removes the self-graded roadmap opt-out entirely rather than patching its judgment call.
- Rejected: "Accountable" or plain "Decision Record" for the acronym (Authoritative fits rationalize-in-place; status already names validity); keeping `/roadmap-review` or renaming to `/review` (misnames the panel; collides with the built-in PR-review command); a "skip if no roadmap" conditional (a self-graded gate opt-out).
- Reopen-if: a consumer reports a remaining hardcoded stack/UI/artifact/process assumption -> fold the fix in place, don't spawn a new ADR. "Authoritative" or "/decide" reads wrong to a consumer -> reopen that naming only.
- Enforced: `pdca-workflow/scripts/adr-lint.mjs` (cite syntax, `status` enum); `docs/decisions/README.md`.
