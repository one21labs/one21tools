# pdca-workflow

A PM-led PDCA (Plan-Do-Check-Act) feedback loop for AI-assisted projects, run by Claude agents:
turn every piece of user feedback into a deliberate decision, build it, verify it against the real
product, then improve the process that produced it.

The goal is **not to remove the human from the loop** — it is to raise the AI's decision quality
(recorded, independently verified, self-improving) so the human can delegate more and intervene
less. The human stays accountable; the agents earn more of the work.

## The loop is the asset

This plugin is an implementation of what the field now calls **loop engineering**: the durable
asset around an AI model is the loop — context, memory, decision records, evals, verification
gates, and the feedback that improves them — not the model, which is a swappable component.
The frame was derived here independently, from TPS/lean and Deming's PDCA applied to a real
repo; the wider field converged on the same shape from the other direction:

- Anthropic on context as a finite engineered resource ([Sept 2025](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents))
  and a planner -> generator -> evaluator harness cycling until the app works
  ([Mar 2026](https://www.anthropic.com/engineering/harness-design-long-running-apps));
  Boris Cherny: "The default isn't 'I'm going to prompt Claude' — the default is now 'I'm going
  to have Claude prompt itself'" (MIT Technology Review, May 2026). Anthropic's "dreaming" — a
  scheduled offline pass that reviews sessions and curates memory — is `/retrospect`'s frame.
- Tom Blomfield's self-improving company loop — sensor / policy / tool / quality gate / learning
  mechanism ([YC, May 2026](https://www.ycombinator.com/library/Qf-how-to-build-a-self-improving-company-with-ai)):
  here, ADRs are the policy layer, verify/red-team the quality gate, retrospect the learning
  mechanism, and hooks/linters the forcing functions.
- The lineage runs back to Karpathy's LLM-OS sketch (2023); Lilian Weng's
  [harness engineering for self-improvement](https://lilianweng.github.io/posts/2026-07-04-harness/)
  (July 2026) argues self-improvement should target exactly this orchestration layer, bounded
  by permissions and observability.

What survives contact with the surveyed field as this stack's actual differentiation (a 2026-07
three-lane survey; pieces like paired with/without skill evals and trigger ablation are NOT
novel — Anthropic's skill-creator and SkillsBench do both): **the integrated loop** — advisor
panel -> PM-authored ADR -> independent verify/red-team gate -> transcript-mined retrospective
that edits the loop's own agents/skills — closed nowhere else as one system; **decisions as
first-class lintable records** (budgeted, back-pointed, revisit-triggered ADRs); and in the
sibling skill-bench harness, **adversarial prosecutor grading** (vs the field's
neutral-by-design graders), **enforced cross-family judging** (advisory-only elsewhere), and
**pre-registration + cost-gating** — verified absent, combined, from every mainstream eval
framework surveyed.

Being different is not being better, and this repo holds its own claims to its own rule
(ADR 0024: an unmeasured process is a cut candidate). Per-claim measured status, on the
source repo's committed benchmarks:
- **prosecutor grading** — measured effect: the battery's uniform prosecutor RAISED the
  skills' with-arm delta (+0.075 -> +0.088) by shaving the baseline's inflated partial
  credit — verdicts get harder to earn, not easier (`2026-07-08-skills-hermetic`).
- **cross-family judging** — earned its keep twice: the #172 prototype flipped its first
  verdict, and the 2026-07 frozen re-grade flipped 1 of 10 recorded primary verdicts
  (`2026-07-17-crossjudge-regrade`); the other 9 held — the instrument detects
  judge-dependence without manufacturing it.
- **pre-registration + cost gates** — observed saves on record (a 3.5x cost-estimate miss
  caught and revised pre-grid, per ADR 0066/0076's paper trail), but NO controlled
  comparison against running without them yet — that is a discipline claim, not a measured
  superiority claim.
- **the integrated loop itself** — NOT yet shown to beat cheaper alternatives. The honest
  measured state is in "Measured" below: specific edges (false-positive halving, failure
  anticipation from independent perspectives) and honest nulls elsewhere; the direct
  panel-vs-single-advisor comparison is queued (#236). Until it runs, "closed nowhere else"
  is a fact about the field, not evidence of value.

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
scripts/       adr-lint.mjs, char-budget.mjs (+ .test.mjs each)
                 the ADR-corpus + doc-budget poka-yoke, hook decision-logic tests (node, zero-dep)
templates/     claude-review.yml           opt-in advisory muda CI (GitHub)
hooks/         hooks.json (model guard, gate-pipe guard, ADR post-edit lint, spawn log)
```

The five meta-roles ship here. The **advisor panel is project-specific** and is generated for
each project by `/pdca-init` from `references/panel-generation.md` — one advisor per distinct way
the product can be wrong, plus the cost / value / risk / differentiation axes.

## Scope — what's generic vs project-supplied

The plugin ships the generic framework; each project supplies its domain (advisor personas,
thresholds, Sacred files, render/verify command). Two deliberate scope calls (recorded in this
repo's decision log as ADR 0001, pdca-workflow-extraction-scope — outside this plugin's shipped
files, so no link survives an install; the framework dogfooded on its own extraction):

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
/pdca-init        # once per project: CLAUDE.md + docs/pdca/ + docs/decisions/ + advisor panel
/decide   # decide a judgment call; writes an ADR
/retrospect       # standing at session close + on demand (ADR 0081); improves the process
```

`/pdca-init` and `/decide` are explicit-invoke only (`disable-model-invocation`) — the panel
spends many agents and writes files, so it never auto-fires. `/retrospect` is model-invocable
but trigger-bound (ADR 0016): it fires only at its ADR 0081 triggers, so the session itself
can discharge — and mark — the standing close-out.

**Hook firing scope (ADR 0071):** the enforcement hooks are per-project opt-in — they no-op
unless the project has the `docs/pdca/` marker (`/pdca-init` creates it; the hooks never do).
Installing the plugin for its skills alone changes nothing in projects that haven't adopted.
To scope the whole plugin (skills included) per project, use Claude Code's native
`enabledPlugins` in the project's `.claude/settings.json`.
