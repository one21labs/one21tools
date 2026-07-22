# one21tools

Claude Code plugins that measure whether their own guidance works: skills are kept, improved, or
reverted by hermetic paired evals — never on faith — plus a PM-led decision workflow whose
records and gates are enforced in CI.

**Goal: quality output, autonomously, judged as the person receiving it.** Two levers, and
everything here serves one of them: raise the measured benefit-per-token of what Claude loads
(quality), or move rules into surfaces that fire without a human catching the miss — gates,
hooks, and skills, not prose (autonomy).

## Install

```
/plugin marketplace add one21labs/one21tools
/plugin install dev-skills@one21tools          # code-standards, building-skills, optimizing-context
/plugin install engineering-skills@one21tools  # engineering-principles (Lean/TPS applied to software)
/plugin install pdca-workflow@one21tools       # /decide /advise /verify /red-team /retrospect /pdca-init
/plugin install skill-bench@one21tools         # /bench — the paired-eval harness that measures the rest
```

Updates: `/plugin marketplace update one21tools`. Or clone and symlink individual skills:
`ln -s /path/to/one21tools/skills/code-standards ~/.claude/skills/code-standards`.

Requirements: the measurement harness needs python3 + node + the `claude` CLI (trigger runs are
Linux/WSL-only); cross-family judging prefers a `grok` CLI and falls back to same-family with a
recorded caveat. Installing the skills alone needs none of that.

## What changes after install

- The engineering skills fire on design, planning, waste, and SSoT questions and push back on
  sunk-cost, premature abstraction, and copy-paste-under-deadline patterns — the behaviors the
  eval battery below actually tests.
- `/decide` runs a PM-led panel and records the call as a linted ADR; `/verify` and `/red-team`
  gate what ships; `/retrospect` mines what went wrong. Records are enforced by `adr-lint`
  (structure, cites, char budgets) — not convention.
- `/bench` measures any skill with paired with/without runs, blind grading, an adversarial
  prosecutor pass, and pre-registered cost ceilings.

## Measured state (the honest block)

Every differentiation claim here carries its measured status; `benchmarks/` holds the
append-only evidence, one dated dir per run.

- `code-standards`: KEEP, strong, judge-robust (2026-07-17 re-measure).
- `engineering-principles`: improved version's benefit +0.206 mean fraction-met delta, 95% CI
  [+0.038, +0.373] excluding zero — hermetic, blind + prosecutor (2026-07-09 re-measure).
  Which content carries that delta (operational triggers vs concepts the model may already
  know) is under measurement (#244).
- `pdca-workflow` panel: honest nulls recorded — rubric-quality ~ cost-matched baselines across
  six instruments; the measured survivors are the process guarantees (forced records, spend
  gates), retrospect's false-positive halving, and an n=1 failure-anticipation edge
  (pdca-workflow/README.md "Measured" section routes the program).
- Cross-family judging: two caught verdict flips, nine robust holds (2026-07-17 re-grade).
- The repo measures itself: `node scripts/scorecard.mjs` computes the decision corpus's
  assumption hit-rate and audit coverage (a compass that fires reviews, never a CI block).

## The improvement loop

1. Each measured skill has `evals/evals.json` (3+ cases, schema-gated).
2. Paired hermetic runs — with/without the skill, no repo access, no installed plugins; a
   non-hermetic run is a recorded confounded null, never a verdict.
3. Blind grading + a prosecutor re-examining every PASS.
4. Verdict: eval-clustered mean delta with a 95% CI, read against token cost. Keep, improve, or
   revert follows the measurement; results land under `benchmarks/<date>-*/`.
5. Description ablation: the always-loaded frontmatter description is trigger-tested separately.

Method home: `skill-bench/skills/bench/references/empirical-evals.md`.

## Gates (required CI)

`gates.yml` runs on every PR: skill shape + char budgets (`validate.py`), decision-log
integrity + doc/agent budgets (`adr-lint.mjs`), every gate script's decision-logic tests,
benchmark workflow checks, cross-file restatement, PR-body guards, and the fetch-audit
requirement for new external references. Judgment calls are decided, not accumulated:
`docs/decisions/` is the ADR log; the repo dogfoods its own `pdca-workflow` for every call
recorded there.

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
