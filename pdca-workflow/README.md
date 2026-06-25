# pdca-workflow

A PM-led PDCA (Plan-Do-Check-Act) feedback loop for AI-assisted projects, run by Claude agents.
The general form of the review system built for LTconfig: turn every piece of user feedback into
a deliberate decision, build it, verify it against the real product, then improve the process
that produced it.

## The cycle

| Phase | What runs |
|-------|-----------|
| **Plan** | `/roadmap-review` — clarify scope, advisors argue (dialectic, opposing counsel on contested calls), the `pm` agent decides and writes an ADR. |
| **Do** | `tech-lead` turns the ADR into a buildable spec; you implement it. |
| **Check** | `verifier` reproduces every load-bearing claim and checks the ADR's `[checkable]` assumptions against the real code/output; `red-team` tries to break it. The gate can BLOCK. |
| **Act** | Ship + bump the version; `/retrospect` folds process learnings back into their lowest home (an agent, a skill, or CLAUDE.md). |

Three jobs are split on purpose — **advise, decide, verify** — because a correctness panel
finds problems but can't decide trade-offs, and averaging hides the one accountable decision.

## What's in the box

```
agents/        pm, tech-lead, red-team, verifier, retrospect   (domain-agnostic meta-roles)
skills/
  roadmap-review/   the decision panel (the workflow's system of record)
    references/adr-template.md
  retrospect/        the Act loop
  pdca-init/         scaffolds a project + generates its advisor panel
    references/       panel-generation, claude-md-template, advisor-template
hooks/         hooks.json + retrospect-reminder.sh  (PR-create -> /retrospect reminder)
```

The five meta-roles ship here. The **advisor panel is project-specific** and is generated for
each project by `/pdca-init` from `references/panel-generation.md` — one advisor per distinct way
the product can be wrong, plus the cost / value / risk / differentiation axes.

## Use it in a project

```
/plugin install pdca-workflow@one21tools
/pdca-init        # once per project: CLAUDE.md + docs/decisions/ + a tailored advisor panel
/roadmap-review   # decide a judgment call; writes an ADR
/retrospect       # before opening a PR; improves the process
```

All three skills are explicit-invoke only (`disable-model-invocation`) — the panel spends many
agents and writes files, so it never auto-fires.
