# pdca-workflow

A PM-led PDCA (Plan-Do-Check-Act) feedback loop for AI-assisted projects, run by Claude agents:
turn every piece of user feedback into a deliberate decision, build it, verify it against the real
product, then improve the process that produced it.

The goal is **not to remove the human from the loop** — it is to raise the AI's decision quality
(recorded, independently verified, self-improving) so the human can delegate more and intervene
less. The human stays accountable; the agents earn more of the work.

## The cycle

| Phase | What runs |
|-------|-----------|
| **Plan** | `/decide` — clarify scope, advisors argue (dialectic, opposing counsel on contested calls), the `pm` agent decides and writes an ADR. |
| **Do** | `tech-lead` turns the ADR into a buildable spec; you implement it. |
| **Check** | `verifier` reproduces every load-bearing claim and checks the ADR's `[checkable]` assumptions against the real code/output; `red-team` tries to break it. The gate can BLOCK. |
| **Act** | Ship + bump the version; `/retrospect` folds process learnings back into their lowest home (an agent, a skill, or CLAUDE.md). |

Three jobs are split on purpose — **advise, decide, verify** — because a correctness panel
finds problems but can't decide trade-offs, and averaging hides the one accountable decision.
The panel pieces also ship standalone — `/advise`, `/verify`, `/red-team` — for calls that
need one right-sized check, not the ceremony; `/decide` composes them and adds the record.

**Measured (2026-07, six instruments; `benchmarks/2026-07-1{2,3,4}-pdca-*` in the source repo):**
`/retrospect` shows no recall/triage edge over a bare reviewer on seeded defects — on
discriminating substrates with a triage-aware metric the delta is ~zero under both judge
families — but reproducibly asserts HALF the false findings (FP guard, both versions).
`/decide` shows no rubric-quality edge over a token-matched deliberation prompt
(judge-sensitive: +0.010 same-family; the cross-family re-grade moves it positive — direction
only, prototype basis per ADR 0057; CIs straddle zero); a 7x-cheaper
decider+probes replacement failed all pre-registered quality bars across a 3-iteration
improvement loop under BOTH judges; a poker/Delphi numeric-estimation round at 0.29x cost
failed three of four bars under BOTH judges (its planted-trap losses trace mostly to a
decider output-capture defect — that benchmark's post-verdict correction; the surviving
gap is record richness) — the panel's one measured edge is failure anticipation from genuinely independent
perspectives (solo self-argument collapses it; both cheap substitutes died on it), with high
per-run variance and NO run-to-run variance damping (three same-config runs: panel scenario
spread ~ bare spread). A mechanical DoD record check predicts record quality among bare
records only (+0.21/+0.23 both corpora); panel records satisfy its items by construction.
Measured value so far: process guarantees, FP discipline, and that independence edge — not
per-decision quality, not consistency. Follow-up: ADR 0057/0061; live successors #184, #186
Phase-1.

## What's in the box

```
agents/        pm, tech-lead, red-team, verifier, retrospect   (domain-agnostic meta-roles)
skills/
  decide/   the decision panel + the process system-of-record
    references/       adr-template, adr-lint, metrics-engine, doc-budgets
  advise/ verify/ red-team/   the panel primitives, standalone (decide composes them)
  retrospect/        the Act loop
  pdca-init/         scaffolds a project + generates its advisor panel
    references/       panel-generation, claude-md-template, advisor-template
scripts/       adr-lint.mjs, char-budget.mjs (+ .test.mjs each), retrospect-reminder.test.mjs
                 the ADR-corpus + doc-budget poka-yoke, hook decision-logic tests (node, zero-dep)
templates/     claude-review.yml           opt-in advisory muda CI (GitHub)
hooks/         hooks.json + retrospect-reminder.sh   (PR-create -> /retrospect reminder)
```

The five meta-roles ship here. The **advisor panel is project-specific** and is generated for
each project by `/pdca-init` from `references/panel-generation.md` — one advisor per distinct way
the product can be wrong, plus the cost / value / risk / differentiation axes.

## Scope — what's generic vs project-supplied

The plugin ships the generic framework; each project supplies its domain (advisor personas,
thresholds, Sacred files, render/verify command). Two deliberate scope calls (recorded in this
repo's [docs/decisions/0001](../docs/decisions/0001-pdca-workflow-extraction-scope.md), the
framework dogfooded on its own extraction):

- **Metrics engine = spec, not code.** `references/metrics-engine.md` is the language-neutral
  `analyze()` contract (window-decoupling, sample-gating, `unknown != healthy`); a project
  implements it in its own stack against its own analytics provider. The runnable form is too
  stack/provider-specific to ship.
- **No standalone `review-system.md`.** The `/decide` skill IS the process
  system-of-record — there is no separate process doc to drift against.

## Why it stays alive

A process rots unless it is **committed** (version control survives), **auto-discovered**
(CLAUDE.md points to it), and **executable** (a `/`-command runs it; a test or linter gates it).
This plugin keeps all three wired, and ADR revisit triggers pull stale decisions back each run.

## Use it in a project

```
/plugin install pdca-workflow@one21tools
/pdca-init        # once per project: CLAUDE.md + docs/decisions/ + a tailored advisor panel
/decide   # decide a judgment call; writes an ADR
/retrospect       # before opening a PR; improves the process
```

All three skills are explicit-invoke only (`disable-model-invocation`) — the panel spends many
agents and writes files, so it never auto-fires.
