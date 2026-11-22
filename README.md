# one21tools

Claude Code plugins that measure whether their own guidance works: skills are kept, improved, or
reverted by hermetic paired evals at dated baselines — plus a PM-led decision workflow whose
records and gates are enforced in CI.

**Goal: quality output, autonomously, judged as the person receiving it.** Two levers, and
everything here serves one of them: raise the measured benefit-per-token of what Claude loads
(quality), or move rules into surfaces that fire without a human catching the miss — gates,
hooks, and skills, not prose (autonomy).

## Install

**Claude Code (terminal):**

```
/plugin marketplace add one21labs/one21tools
/plugin install dev-skills@one21tools          # code-standards, building-skills, optimizing-context
/plugin install engineering-skills@one21tools  # engineering-principles (Lean/TPS)
/plugin install pdca-workflow@one21tools       # /decide /advise /verify /red-team /retrospect /sweep /pdca-init /MSH /improve
```

**Claude desktop app (Chat, Cowork, Code):** open Customize, select Plugins, select Add, select
Add marketplace, enter `one21labs/one21tools`, then install the plugins you want. In the Code tab
the terminal commands above also work typed into a session.

**Cloud sessions (Claude Code on the web):** a cloud session loads the plugins turned on for your
account in the desktop app, as above. It does NOT install plugins a repository enables in its
`.claude/settings.json` — so turn `pdca-workflow` on for your account, or its skills, agents and
guards are absent from every cloud session, including ones on a repo that ran `/pdca-init`.

What loads where:

| Surface | Skills and commands | `pdca-workflow` agents | `pdca-workflow` guards |
|---|---|---|---|
| Claude Code in a terminal; desktop app, Code tab | Yes | Yes | Yes (run in a terminal session: a helper spawned with no model ran on Sonnet) |
| Desktop app, Cowork | Yes | Yes, per Anthropic's platform table | Yes, per the same table; not run by us |
| Desktop app, Chat | Yes | No | No |
| Cloud session | Yes | Not confirmed | Not confirmed |

Without the agents, each role still gets its own model: `pdca-workflow/skills/decide/SKILL.md`
(Roles) owns the fallback. The scripts need `node`; the guards also need
`bash`, which on Windows means Git for Windows. All four plugins from this repo and
skill-measure install side by side with no shared names.

Updates: `/plugin marketplace update one21tools`. Installs added before 27-Jul-2026 predate a
history rewrite and cannot update — remove and re-add the marketplace once. Or clone and symlink
individual skills:
`ln -s /path/to/one21tools/skills/code-standards ~/.claude/skills/code-standards`.

Each plugin installs standalone: no manifest `dependencies` unless a plugin cannot function
without another's files (none today). The harness that measures these skills (`/bench`) is its
own repo and install, [one21labs/skill-measure](https://github.com/one21labs/skill-measure):
it reads each skill's `evals/evals.json` here as it is, and needs the `claude` command-line
program, so it runs in a terminal or the desktop app's Code tab, not in Chat.

## What changes after install

- The engineering skills fire on design, planning, waste, and SSoT questions and push back on
  sunk-cost, premature abstraction, and copy-paste-under-deadline patterns — the behaviors the
  eval battery below actually tests.
- `/decide` runs a PM-led panel and records the call as a linted ADR; `/verify` and `/red-team`
  gate what ships; `/retrospect` mines what went wrong. Records are enforced by `adr-lint`
  (structure, cites, char budgets) — not convention.
- With skill-measure installed, `/bench` measures any skill with paired with/without runs and
  spend gates; its verdict path adds blind grading and an adversarial prosecutor pass.

## Measured state

What each plugin's evidence supports today. Numbers, intervals and judges live in the dated
directory each row names (`benchmarks/` is append-only, one directory per run). Read every "helps"
as "beat the bare model against the skill's own expectations": those expectations were written
with the skill in view, a confirmed bias (#317, ADR 0101), and the harness audit is still open
(one21labs/skill-measure#1). Each verdict measured the skill text AS OF its dated directory;
`git log --since=<dir-date> -- skills/<name>` lists what changed since (ADR 0095).

| Plugin part | What the evidence supports | Evidence |
|---|---|---|
| `code-standards` | Helps, and the verdict held under a second, different-vendor judge. A 12-Oct re-run agrees on Sonnet 5.5 but is not promoted (same-family judge); its Opus 5.5 pair is unmeasured. | `benchmarks/2026-07-17-code-standards-remeasure/`, `benchmarks/2026-10-12-g8-shortfall/` |
| `engineering-principles` | Probably helps; not freshly proven. The slim version that ships was shown no worse than the longer version that was proven, but its own interval includes zero. The operational rules carry the effect; concepts the model already knows add nothing measurable. | `benchmarks/2026-07-18-ep-slim-remeasure/`, `benchmarks/2026-07-09-ep-remeasure-hermetic/`, `benchmarks/2026-07-18-ep-partition/` |
| `building-skills` | Unsettled: one judge says it helps, the headline judge is inconclusive. A revision missed its pre-registered bar and was reverted. | `benchmarks/2026-07-18-bs-iter3-remeasure/`, `benchmarks/2026-10-12-g8-shortfall/` |
| `optimizing-context` | Unmeasured on the current instrument (ADR 0100). | `benchmarks/2026-10-12-g8-shortfall/` |
| `pdca-workflow` | The decision panel does not beat a cost-matched plain prompt on decision quality. What did measure: `/retrospect` asserts fewer false findings, and independent advisors anticipate failures a single voice misses. | `pdca-workflow/README.md`, "Measured" |

## The improvement loop

Method home: `one21labs/skill-measure:skills/bench/references/empirical-evals.md`.

## Gates (required CI)

`.github/workflows/gates.yml` runs on every PR; its step names are the gate list.
`docs/decisions/` is the ADR log.

## Where the ideas come from

Lean/TPS/Deming, applied: waste elimination becomes YAGNI and SSoT enforcement; poka-yoke
becomes gates that make the error impossible rather than detected; "build quality in" becomes
catching defects at source. The skills encode these as directives — and the measured state above is what
keeps them honest.

## Provenance

What comes from whom (ADR 0085): the repo owner supplies the direction, the principles, and the
requirements; Claude produces the implementation — code, prose mechanics, records — under that
direction. This default speaks for the whole repo. Where it fails for a doc read standalone, that
doc carries a single inline note at the point of deviation (exemplar:
`skills/engineering-principles/references/ENGINEERING_PRINCIPLES.md`).

## License

MIT — see [LICENSE](LICENSE).
