# one21tools

Four small Claude Code skills, kept to what measurement supports.

This repo used to ship much more: a decision panel with decision records and a linter, guard
hooks, a project scaffolder, and two large reference skills. Its own benchmarks showed that most
of that did not change what the model does, so on 23-Nov-2026 it was cut to the parts that did.
What was removed, and the evidence, is at the end.

## What is here

| Plugin | Skill | What it does | What the evidence says |
|---|---|---|---|
| `dev-skills` | `code-standards` | A house style for code: file headers, naming, error handling, logging, function size. | Helps. Beat the bare model by +0.44 (95% interval +0.19 to +0.69) with a different vendor's model as judge. The gain is on tasks written with the skill in view, so read it as "reliably applies this style", not "writes better code". |
| `engineering-skills` | `engineering-principles` | Four working rules: approved is not complete; a person's mistake is not a root cause; one definition per fact; time already spent is not a reason to finish. | Rewritten on 23-Nov-2026 from the rules that carried the measured effect in the longer version (+0.21, interval includes zero; the conceptual material added nothing). The rewrite has not been measured. |
| `pdca-workflow` | `/advise` | Before a contested decision: state your own pick, get two independent opposing views, report what they changed. | Independent advisors did not choose better options than one careful pass. They anticipated the real failure more often: 0.42, against 0.25 bare and 0.08 for one agent arguing with itself (four cases, small sample). |
| `pdca-workflow` | `/fresh-check` | Before work ships: a reviewer with no stake reproduces the claims and tries to break it. | Not measured. Kept because fresh reviewers given the work, and not the author's conclusions, kept finding real defects while this repo was being built. |

The four skills are about 13 KB of text in total. There are no hooks, agents or scripts in any
plugin.

## Install

In Claude Code:

```
/plugin marketplace add one21labs/one21tools
/plugin install dev-skills@one21tools
/plugin install engineering-skills@one21tools
/plugin install pdca-workflow@one21tools
```

In the Claude desktop app: open Customize, select Plugins, select Add, select Add marketplace,
enter `one21labs/one21tools`, then install the plugins you want.

A cloud session (Claude Code on the web) loads the plugins turned on for your account, not the
ones a repository enables in its settings.

`/advise` and `/fresh-check` start subagents, so they need a surface that has them (Claude Code
in a terminal, the desktop app's Code tab, Cowork). Where there are none, each skill says so
instead of pretending.

Updates: `/plugin marketplace update one21tools`. The plugin names are unchanged from before the
cut, so existing installs update in place. Skills that were removed disappear on update.

## Measuring a skill

The measurement harness is its own plugin,
[one21labs/skill-measure](https://github.com/one21labs/skill-measure). Its `/bench` runs a skill
against the bare model on the cases in the skill's `evals/evals.json` and reports the difference
with an interval. `code-standards` and `engineering-principles` carry their cases here.

The rule this repo now follows: a skill stays if it beats the bare model on cases written
without the skill in view, and goes if it does not.

## What was removed, and why

| Removed | Why |
|---|---|
| `/decide` (advisor panel, decider, decision records, record linter) | No better than a plain "think carefully" prompt on decision quality (+0.01, interval -0.18 to +0.20), at about four times the cost of a bare decision. |
| `/verify`, `/red-team` | Merged into `/fresh-check`. |
| `/retrospect`, `/sweep`, `/pdca-init`, the improve loop, the guard hooks | Unmeasured, or measured with no effect on recall; they mostly maintained the process around them. |
| `optimizing-context` | Inconclusive on every run (+0.003 to +0.10, each interval includes zero) for 53 KB of guidance that restated product documentation and went stale: fifteen wrong statements were found in it and `building-skills` in two days. |
| `building-skills` | Unsettled results, and it overlaps Anthropic's own skill-creator. Its validator stays as this repo's CI check. |
| The benchmark output (22 MB) | Moved out of the plugin repo. |

Across all the skills, the gain on cases written with the skill in view was +0.37. On cases
written blind it was +0.04, with the bare model already at 0.82. The current model does most of
this unprompted. Short rules that tell it what to do in a specific situation moved behaviour;
doctrine, panels and ceremony did not.

The write-ups behind every number here are in skill-measure under `evidence/`. The removed code
and the raw benchmark output remain in this repo's history: the last commit that contains them
is `0a1834d`.

## License

See `LICENSE`.
