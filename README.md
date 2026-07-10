# one21tools

Claude Code skills for software development and engineering workflows.

**Goal: quality output, autonomously.** Claude Code as a real assistant that needs minimal
direction and correction, and self-improves through the measured loop below — so mistakes reduce
and quality rises over time. Everything here serves one of those two levers: raise the measured
benefit-per-token of what Claude loads (quality), or move rules into surfaces that fire without a
human catching the miss — shipped gates, hooks, and skills, not prose (autonomy). Work is
prioritized against them.

Built on manufacturing engineering principles — Lean, TPS, Deming — applied to AI-assisted development. Every skill is designed to give Claude the right context at the right altitude: no redundancy, no noise, no content Claude already knows. That token efficiency is enforced, not aspirational: documentation is held to CI-checked character budgets.

The differentiating idea: manufacturing quality principles translate directly to AI-assisted code. Lean's waste elimination becomes YAGNI and SSoT enforcement. Toyota's poka-yoke becomes boundary validation. Deming's "build quality in" becomes catching defects at source rather than inspecting them out downstream. The skills encode these as Claude directives.

## Skills

| Skill | What it does |
|-------|--------------|
| `code-standards` | Language-agnostic code quality standards: file headers, naming, error handling, logging. SSoT and altitude as the governing tests for what belongs in a comment. |
| `engineering-principles` | Lean/TPS/Deming manufacturing principles applied to software, documentation, and process. Includes context engineering mapped to TPS. |
| `building-skills` | Framework for creating, testing, and validating Claude Code skills. Covers conciseness, description-as-instruction, and iterative testing — plus the empirical skill-improvement loop below. |
| `optimizing-context` | Patterns for structuring Claude's context efficiently: CLAUDE.md, skills, plugins, subagents, MCP, hooks. |

## The skill-improvement loop

Skills here are not shipped on faith — each one carries an eval set and gets measured, and the
measurements exist to **improve** the skills (raise benefit-per-token), not just gatekeep them.
The loop (method home: `skills/building-skills/references/empirical-evals.md`; decision records:
ADR 0019, 0023, 0024, 0025 in `docs/decisions/`):

1. **Evals** — every skill has `evals/evals.json` (3+ cases, schema-gated by `validate.py`).
2. **Hermetic paired benchmark** — each eval runs with and without the skill under a hermetic
   executor (no installed plugins, no repo file access; ADR 0023 — a non-hermetic run is a
   recorded confounded null, never a verdict).
3. **Blind grading + prosecutor** — a grader blind to the arm scores each response against the
   eval's expectations; every PASS is re-examined adversarially.
4. **Verdict** — eval-clustered mean delta with a 95% CI, read against token cost
   (`skills/building-skills/scripts/eval_verdict.py`). Keep, improve, or revert follows the
   measurement (ADR 0024); results land as append-only snapshots under `benchmarks/<date>-*/`.
5. **Description ablation** — the frontmatter description is the one always-loaded surface, so it
   is trigger-tested separately (TP/FP on should-fire and adjacent should-not-fire queries) and
   trimmed to the shortest text that holds recall
   (`skills/building-skills/references/description-ablation.md`).

All of this machinery is in-repo and self-contained (python3 + node + the `claude` CLI; trigger
runs are Linux/WSL-only). No external skill or plugin needs to be installed to run it —
`evals.json` keeps the upstream skill-creator schema for provenance, but execution no longer
depends on skill-creator (ADR 0033).

## Test machinery and gates

| Piece | Where | What it enforces / does |
|-------|-------|------------------------|
| `validate.py` | `skills/building-skills/scripts/` | Skill shape: frontmatter, char budgets, emoji ban, eval schema. Run on every skill in CI. |
| `eval_verdict.py` | `skills/building-skills/scripts/` | Benchmark JSON -> cost-per-benefit verdict; audits raw-sample completeness (ADR 0023). |
| `run_eval.py` | `skills/building-skills/scripts/` | Vendored trigger runner (description ablation instrument; ADR 0033). |
| `benchmarks/lib/` | repo root | Shared benchmark IO + verdict math (`bench_io.py`, `verdict.py`), unit-tested. |
| `adr-lint.mjs` | `pdca-workflow/scripts/` | Decision-log integrity: frontmatter, ids, cites, char budgets. |
| `check-workflow.mjs` | `scripts/` | Benchmark workflow files: syntax + explicit `model:` on every agent call (ADR 0029). |
| `check-pr-body.mjs` | `scripts/` | Required `Retrospective:` line on every PR (ADR 0030). |
| `gates.yml` | `.github/workflows/` | Runs all of the above as the required CI check (ADR 0012). |

Judgment calls are decided, not accumulated: `docs/decisions/` is the ADR log (one decision per
record, linted, version-agnostic). The repo dogfoods its own `pdca-workflow` plugin for this.

## PDCA workflow plugin

`pdca-workflow` packages a PM-led feedback loop you can drop into any project — a Deming
Plan-Do-Check-Act cycle run by Claude agents. It is the general form of the system built for
LTconfig.

| Component | What it is |
|-----------|------------|
| `/decide` skill | The decision panel: advisors argue, one PM decides and writes an ADR, an independent gate verifies, red-team breaks it. Triggered by any user feedback or open judgment call. |
| `/advise`, `/verify`, `/red-team` skills | The panel primitives standalone: situational advice, independent verification, adversarial break — right-sized checks without the ADR ceremony. `/decide` composes them. |
| `/retrospect` skill | Automates the Act loop: reads git history + session friction, emits routed process improvements. Run before opening a PR. |
| `/pdca-init` skill | Scaffolds the workflow into a project: a themed CLAUDE.md, the ADR decision log, and a **project-tailored advisor panel** generated from the project's domain. |
| Agents | The domain-agnostic meta-roles: `pm`, `tech-lead`, `red-team`, `verifier`, `retrospect`. The advisor panel itself is generated per project by `/pdca-init`. |
| ADR system + linter | A version-agnostic, frontmatter-cataloged decision-record template (one-ADR-per-PR, fetch-then-max numbering, rationalize-in-place) and `adr-lint.mjs` — a zero-dependency node guard against bad frontmatter, duplicate IDs, dangling cites, and over-budget docs (char budgets on the ADR corpus and CLAUDE.md). |
| Metrics engine spec | `metrics-engine.md` — a language-neutral `analyze()` contract mapping usage thresholds to PDCA triggers; each project implements it in its own stack. |
| Hook | A non-blocking reminder to run `/retrospect` when you create a PR. |

After installing, run `/pdca-init` once per project to generate its CLAUDE.md and advisor panel,
then `/decide` to decide your first judgment call. See
[pdca-workflow/README.md](pdca-workflow/README.md).

## Install

Add the marketplace and install plugins from within Claude Code:

```
/plugin marketplace add one21labs/one21tools
/plugin install dev-skills@one21tools
/plugin install engineering-skills@one21tools
/plugin install pdca-workflow@one21tools
```

`dev-skills` bundles code-standards, building-skills, and optimizing-context. `engineering-skills` bundles engineering-principles. `pdca-workflow` adds the PM-led feedback loop (agents, skills, and a hook) — see the section above.

To get updates after installation:

```
/plugin marketplace update one21tools
```

Or clone and symlink individual skills without the plugin system:

```bash
git clone https://github.com/one21labs/one21tools.git
ln -s /path/to/one21tools/skills/code-standards ~/.claude/skills/code-standards
```

## License

MIT — see [LICENSE](LICENSE).
