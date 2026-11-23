# Handoff

Written 23-Nov-2026 on `claude/brave-pasteur-4ho96t`, after `0c5117b`. Rewrite this file whole
each turn (`pdca-workflow/commands/improve.md`). Where it disagrees with git or the tracker, they
win.

Goal (`README.md`): quality output, autonomously, judged as the person receiving it.

## Measures

| Measure | Baseline `d4bcbc2` | Now | Target |
|---|---|---|---|
| Shipped skills with a promoted "helps" verdict | 1 of 5 | 1 of 4 | all, none below bare |
| Known wrong statements in shipped guidance on `main` | not counted | 15, fixed on this branch | 0 |
| Internal record or issue numbers in shipped, model-loaded text | 37 | 0 | 0 |
| Shipped guidance, bytes | 218,629 | 211,650 | below baseline |
| Gate and hook code with tests, bytes | 344,073 | 312,943 | below baseline |
| Everything outside `benchmarks/`, bytes | 926,255 | 798,239 | falling |
| Decision records | 24 at `c1f0bde` | 19 | only live decisions |
| Paneled records carrying an `Effect:` line | none | 0 | read at ten |

How to read them: verdicts from the README "Measured state" table; cites with
`grep -rnE 'ADRs? [0-9]{4}|#[0-9]{2,3}\b'` over `skills/*/SKILL.md`, `skills/*/references`,
`pdca-workflow/{skills,agents,commands}`; guidance bytes with `wc -c` over the same set; gate
bytes over `scripts/*.mjs`, `pdca-workflow/{scripts,hooks}`, `.claude/hooks`, `validate*.py`,
`gates.yml`; the total with `git ls-files -- . ':!benchmarks'`; `Effect:` with
`grep -l '^- Effect:' docs/decisions/[0-9]*.md`. All read at `0c5117b`.

## State

Pull request #340 is open and NOT merged; merging is the owner's call. Beyond the 22-Nov
follow-up it now carries:

- **`/decide` sorts first** (ADR 0062, Decision 5). Four exits, first fit: ask the person,
  inherit a record, panel, inline. On the panel exit the session says `Pick alone:` on the sort
  line, `advise` runs TWO opposing advisors, and the record gets an `Effect:` line: what
  advice, PM and check each changed. `retrospect` reads those lines.
- Five more product statements corrected.
- The adopter CLAUDE.md template no longer ships the retired "never fix directly" rule.

Nine headless runs in scratch clones (Sonnet): the ask and inline exits cost $0.11 to $0.27 with
no helpers; five panel runs cost $0.71 to $1.15, and the last followed every step. Unproven:
whether the self-reported `Effect:` line prices the panel honestly; nothing ran in the desktop app.

Checking the two repos together: install the four plugins into a
scratch `CLAUDE_CONFIG_DIR` whose path has a space; start `claude -p --output-format stream-json
--verbose` and read the `init` event; spawn a helper with no model and confirm
`docs/pdca/gate-hits.txt` gains a line; load each `skills/*/evals/evals.json` through
skill-measure's `bench_skill.load_evals`; run `validate.py` over its `skills/bench`.

## Next candidates, ranked

1. **Read the `Effect:` lines at ten paneled records.** A stage reading `nothing` ten times
   running is cut; the separate `pm` spawn is the one on trial.
2. **The guards are bash**, so Windows needs Git for Windows; a node rewrite removes that.
3. **`validate.py` runs on Python 3.9 but no check holds it there.**

Also: #337 needs a rebase; a shell edit bypasses the budget guard, and the guard is off in a session started outside the repo
root, so CI is the catch; the `agentskills.io` rows in `validation-rules.md` are unchecked.

## Waiting on the owner

- Merge #340, or say what to change.
- Turn `pdca-workflow` on for the account, then try `/pdca-workflow:decide` and `/bench` in the
  desktop Code tab and in Cowork.
- `claude setup-token`: for the #328 re-measure and a verdict on the two unmeasured skills.
- The scheduled task "one21tools self-improvement loop" is OFF: give it this repository with
  push access, then turn it on.
- Decide: ADR 0024 against the sunk-cost ruling; where frozen benchmark evidence lives (22 MB);
  #338 item 3; whether the 90% pause rule also covers the weekly limit.
