---
id: 0064
title: "Hook decision-logic tests standardize on sibling test-<basename>.sh"
status: accepted
tier: lite
summary: "New bash hooks are tested by a self-contained gates.yml-invoked sibling test-<basename>.sh, never a new <basename>.test.mjs; the pre-existing .mjs-tested hook is grandfathered by name. The enumerator enforcing this was deleted 2026-07-27 (#311); gates.yml runs the suites. Closes #155."
---

# 0064 — hook decision-logic tests standardize on test-<basename>.sh

- Decision: every newly registered bash hook carries a self-contained sibling
  `test-<basename>.sh` suite picked up by gates.yml's existing `for t in
  .../test-*.sh` steps; the `<basename>.test.mjs` convention is closed to new
  hooks, grandfathered only for `explicit-model-guard.sh` (rewriting its
  working test is muda).
- Why: a hook IS a bash script — the .sh suite tests it in its own language,
  exactly as the harness invokes it, runs on git-bash/WSL2 where the
  node-spawns-bash tests are Windows-skipped locally, and auto-wires into CI by
  glob; the corpus had already converged (8 of 10 hook tests, every hook since
  the ADR 0047 hooks wave).
- Enforced: `.github/workflows/gates.yml` runs every `test-*.sh` suite; the static enumerator was deleted 2026-07-27 (#311).
  any non-grandfathered hook lacking a gates.yml-invoked `test-<basename>.sh`;
  decision logic pinned by each suite itself.
