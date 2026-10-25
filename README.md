# one21tools

Claude Code plugins that measure whether their own guidance works: skills are kept, improved, or
reverted by hermetic paired evals at dated baselines — plus a PM-led decision workflow whose
records and gates are enforced in CI.

**Goal: quality output, autonomously, judged as the person receiving it.** Two levers, and
everything here serves one of them: raise the measured benefit-per-token of what Claude loads
(quality), or move rules into surfaces that fire without a human catching the miss — gates,
hooks, and skills, not prose (autonomy).

## Install

```
/plugin marketplace add one21labs/one21tools
/plugin install dev-skills@one21tools          # code-standards, building-skills, optimizing-context
/plugin install engineering-skills@one21tools  # engineering-principles (Lean/TPS), control-narratives (PLC/DCS specs)
/plugin install pdca-workflow@one21tools       # /decide /advise /verify /red-team /retrospect /sweep /pdca-init /MSH
```

The harness that measures these skills (`/bench`) is its own repo,
[one21labs/skill-measure](https://github.com/one21labs/skill-measure) (Claude Code only):

```
/plugin marketplace add one21labs/skill-measure
/plugin install skill-measure@skill-measure
```

Updates: `/plugin marketplace update one21tools` (and `/plugin marketplace update skill-measure`). Installs added before 27-Jul-2026 predate a
history rewrite and cannot update — remove and re-add the marketplace once. Or clone and symlink
individual skills:
`ln -s /path/to/one21tools/skills/code-standards ~/.claude/skills/code-standards`.

Requirements: skill-measure needs python3 + node + the `claude` CLI (trigger runs are
Linux/WSL-only); cross-family judging uses any foreign-vendor CLI you have or wire yourself, and
falls back to same-family with a recorded caveat. Installing the skills alone needs none of that. Each plugin installs standalone: no manifest
`dependencies` unless a plugin cannot function without another's files (none today).

## What changes after install

- The engineering skills fire on design, planning, waste, and SSoT questions and push back on
  sunk-cost, premature abstraction, and copy-paste-under-deadline patterns — the behaviors the
  eval battery below actually tests.
- `/decide` runs a PM-led panel and records the call as a linted ADR; `/verify` and `/red-team`
  gate what ships; `/retrospect` mines what went wrong. Records are enforced by `adr-lint`
  (structure, cites, char budgets) — not convention.
- With skill-measure installed, `/bench` measures any skill with paired with/without runs and
  spend gates; its verdict path adds blind grading and an adversarial prosecutor pass.

## Measured state (the honest block)

Every differentiation claim here carries its measured status; `benchmarks/` holds the
append-only evidence, one dated dir per run. Two open instrument caveats apply to every verdict
below: the harness audit is unconverged (#310) and expectation-authorship coupling is a confirmed,
unresolved validity threat (#317, ADR 0101): read a KEEP as "beats bare against the skill's own
expectations". Each verdict measured the skill AS OF its dated dir — the text may have changed
since; `git log --since=<dir-date> -- skills/<name>` lists exactly what (ADR 0095).

- `code-standards`: KEEP, judge-robust (2026-07-17 re-measure); a 12-Oct re-measure is not
  promoted, and its Opus 5.5 pair is unmeasured (`benchmarks/2026-10-12-g8-shortfall/`).
- `building-skills`: unsettled — the 2026-07-18 baseline measured +0.153 [-0.016, +0.321]
  (INCONCLUSIVE) under the grok headline judge, +0.236 [+0.004, +0.469] KEEP under claude; an
  iter-3 revision missed its pre-registered bar and was reverted
  (`benchmarks/2026-07-18-bs-iter3-remeasure/`); 12-Oct re-measures are not promoted
  (`benchmarks/2026-10-12-g8-shortfall/`).
- `optimizing-context`: unmeasured (ADR 0100; `benchmarks/2026-10-12-g8-shortfall/`). The
  2026-07-09 MERGE ran on an instrument with isolation defects fixed since.
- `engineering-principles`: what SHIPS is the slim operational core (2026-07-18, #248/#249), and
  it ships on a NON-INFERIORITY bar, not a fresh effect proof — slim +0.170, CI [-0.029, +0.370],
  straddling zero at n=6; slim minus full +0.043, CI [+0.016, +0.069], excluding zero in the
  slim's favour under both judges (`benchmarks/2026-07-18-ep-slim-remeasure/`). The
  CI-excluding-zero anchor (+0.206, [+0.038, +0.373], hermetic, blind + prosecutor) measured the
  EARLIER full version on 2026-07-09. The OPERATIONAL partition carries the delta (#244,
  2026-07-18): operational-only +0.207, conceptual-only +0.057 with a CI straddling zero —
  concepts the model already knows are inert (`benchmarks/2026-07-18-ep-partition/`).
- `control-narratives`: unmeasured (no baseline yet).
- `pdca-workflow` panel: honest nulls recorded — rubric-quality ~ cost-matched baselines across
  six instruments; the measured survivors are the process guarantees (forced records, spend
  gates), retrospect's false-positive reduction (a halving in v2, ~12% in v1), and an n=1
  failure-anticipation edge
  (pdca-workflow/README.md "Measured" section routes the program).
- Cross-family judging: two caught verdict flips from two separate re-grades — 1 of 10 primary
  verdicts judge-fragile with nine robust holds (2026-07-17 re-grade), plus the earlier #172
  prototype flip (2026-07-13).
- The repo measured itself with a scorecard until 2026-07-27, when it was deleted for
  gating nothing and never being run by CI (issue #311). Re-decide before rebuilding one.

## The improvement loop

Method home: `one21labs/skill-measure:skills/bench/references/empirical-evals.md`.

## Gates (required CI)

`.github/workflows/gates.yml` runs on every PR; its step names are the gate list.
`docs/decisions/` is the ADR log.

## Where the ideas come from

Lean/TPS/Deming, applied: waste elimination becomes YAGNI and SSoT enforcement; poka-yoke
becomes gates that make the error impossible rather than detected; "build quality in" becomes
catching defects at source. The skills encode these as directives — and the loop above is what
keeps them honest.

## Provenance

What comes from whom (ADR 0085): the repo owner supplies the direction, the principles, and the
requirements; Claude produces the implementation — code, prose mechanics, records — under that
direction. This default speaks for the whole repo. Where it fails for a doc read standalone, that
doc carries a single inline note at the point of deviation (exemplar:
`skills/engineering-principles/references/ENGINEERING_PRINCIPLES.md`).

## License

MIT — see [LICENSE](LICENSE).
