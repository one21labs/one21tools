---
id: 0102
title: "skill-measure leaves for its own repo; one21tools becomes the Desktop/Cowork-installable toolkit"
status: accepted
summary: "Extract skill-measure/ to one21labs/skill-measure with history; one21tools drops the entry (renames -> null), the skill-bench shim, and the cross-plugin parity test. benchmarks/ stays as the evidence for one21tools' claims; frozen dirs reproduce at their own commit."
---

# 0102 — extract skill-measure to its own repo

- Date: 2026-10-25
- Owner: PM (owner decided repo, name, and scope in-session)
- Panel: none spawned — the owner made the contested calls; one fresh adversary per ADR 0062.
- Context: the one21tools marketplace serves two audiences. Its toolkit plugins suit Claude
  Desktop/Cowork; skill-measure shells out to `claude -p`, promptfoo, grok and copilot
  (`skill-measure/scripts/run_eval.py`, `lib/judge.py`) — a CLI-only dev tool listed beside
  them. A second marketplace in this repo cannot be added from the CLI or Cowork (needs a
  `path` in `extraKnownMarketplaces`), so separation means a repo. A `skill-bench` symlink
  (ADR 0097 Act) makes the tree read as two folders.

## Decision
1. **New repo `one21labs/skill-measure`**, full history (`git filter-repo`, folding the
   `skill-bench/` era in). Its root is the plugin AND a one-plugin marketplace
   (`source: "./"`); install = `/plugin marketplace add one21labs/skill-measure` then
   `/plugin install skill-measure@skill-measure`, in both READMEs. Name kept: SkillLab and
   skill-benchmark collide in-niche (PyPI `skill-lab`; langchain-ai/skills-benchmarks).
2. **Order**: the new repo is live, its CI green and its install verified BEFORE the one21tools
   PR merges. The repo is created only on the owner's go.
3. **one21tools drops it**: marketplace entry removed, `renames` gains `"skill-measure": null`
   (chain `skill-bench` -> `skill-measure` -> null); `skill-measure/` and the `skill-bench`
   symlink deleted; gates.yml loses every harness member (skill-gate glob, harness tests, node glob, check-workflow);
   building-skills tests run via `unittest discover` (43 tests, no reachability guard needed).
4. **benchmarks/ stays** — the evidence for one21tools' claims (README measured block). Frozen
   dated dirs stay byte-identical and reproduce at their own commit (one line,
   benchmarks/README.md). The forwarders keep their paths (ADR 0089 executable-shim rule):
   `benchmarks/lib/` shims resolve the harness from `SKILL_MEASURE_ROOT` and fail with the clone
   command when unset; the `eval_verdict.py` stub exits with the clone command. Templates do the same and
   new dirs record the harness sha.
5. **check-relocated-paths** declares `skill-bench/` and `skill-measure/` DEPARTED: a frozen
   cite under them reports as external (reproduce at commit), not stranded and no longer
   invisible — 8 `skill-bench/` cites were unchecked (symlink, not a dir). Tested.
6. **Parity test retired** (`scripts/check-family-parity.test.mjs`): two repos, two products,
   each owns its family table and tests; crosscheck.mjs's TWIN note cut.
7. **Decision history stays here**; live cites repo-qualify as `one21labs/skill-measure:<path>`,
   the form the plugin already uses for one21tools (its `empirical-evals.md`). Frozen
   dirs and `docs/pdca/*.jsonl` logs untouched. Open harness issues (#310, #252) transfer.

## Justification
The receiving person decides it: a Cowork user should see only plugins that run there; a skill
author gets a one-line install of a product that stands alone. Installs are near zero, so the
migration is cheapest now (ADR 0097's reasoning). Reproduce-at-commit costs nothing a frozen dir
uses — it records what ran, and its commit is exactly that state.

## Assumptions
- [verified] Cowork and `/plugin marketplace add` read only the root marketplace.json; a nested
  one needs `extraKnownMarketplaces` + `path` (code.claude.com plugins/marketplace-reference).
- [verified] removing both dirs, the forwarders, and the stub strands 6 frozen cites (forwarders
  and stub 5, a MOVED marker 1) — scratch-worktree run; kept forwarders + DEPARTED clear them.
- Cross-family red-team (copilot, gpt-6-luna; grok unauthenticated): 5 findings, all taken —
  CI members, executable shims, two-step install, templates, reachability. Parity retirement
  FRAME-UNCHECKED. Probed: grok, copilot.
- [verified] blank-config sim (directory-source one21tools, main -> this branch): an installed
  `skill-measure@one21tools` drops from `enabledPlugins`, lists disabled, uninstalls clean; the
  published repo installs via `marketplace add` + `install`.
- [checkable] **WEAKEST:** the same holds for a GitHub-source install — owner: owner after
  merge; result: pending — named signal: the owner's next session after `/plugin marketplace update`.
- [verified] the split stands alone: its CI (harness tests, node test, check_reachability,
  `claude plugin validate`) is green on one21labs/skill-measure main.
- [unverifiable] skill-measure fails or misleads in Cowork — REOPEN-IF: it is shown to run there
  (the split is then scope only, still owner-wanted).

## Rejected alternatives
- Second marketplace in this repo — no CLI or Cowork add path; unconfirmed source resolution.
- Leave it, label it Claude Code-only — the toolkit's listing still shows a tool Cowork cannot run.
- Move benchmarks/ with the harness — one21tools' claims would cite a sibling repo.
- Rewrite frozen dirs' paths — falsifies the record (ADR 0097 decision 4).
- Git submodule at `skill-measure/` — keeps two-repo coupling and the folder the owner wants gone.

## Revisit triggers
- The owner's install does not migrate -> restore the entry as a `github` source to the new repo.
- A grader family misclassification traced to table drift -> reinstate a parity check.
