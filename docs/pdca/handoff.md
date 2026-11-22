# Handoff

Written 22-Nov-2026 on `claude/brave-pasteur-4ho96t`, after `9860acd`. Rewrite this file whole
each turn (`pdca-workflow/commands/improve.md`). Where it disagrees with git or the tracker, they
win.

Goal (`README.md`): quality output, autonomously, judged as the person receiving it.

## Measures

| Measure | Baseline `d4bcbc2` | Now | Target |
|---|---|---|---|
| Shipped skills with a promoted "helps" verdict | 1 of 5 | 1 of 4 | all, none below bare |
| Known wrong statements in shipped guidance on `main` | not counted | 10, fixed on this branch | 0 |
| Internal record or issue numbers in shipped, model-loaded text | 37 | 0 | 0 |
| Shipped guidance, bytes | 218,629 | 211,024 | below baseline |
| Gate and hook code with tests, bytes | 344,073 | 313,011 | below baseline |
| Everything outside `benchmarks/`, bytes | 926,255 | 795,248 | falling |
| Decision records | 24 at `c1f0bde` | 19 | only live decisions |
| `CLAUDE.md` chars against its 6,000 cap | 5,637 | 5,772 | headroom of 300 |

How to read them: verdicts from the README "Measured state" table; cites with
`grep -rnE 'ADRs? [0-9]{4}|#[0-9]{2,3}\b'` over `skills/*/SKILL.md`, `skills/*/references`,
`pdca-workflow/{skills,agents,commands}`; guidance bytes with `wc -c` over the same set; gate
bytes over `scripts/*.mjs`, `pdca-workflow/{scripts,hooks}`, `.claude/hooks`, `validate*.py`,
`gates.yml`; the total with `git ls-files -- . ':!benchmarks'`. All read at `9860acd`.

## State

Merged 22-Nov on the owner's instruction: #339 as `c1f0bde`, `one21labs/skill-measure#12` as
`f438f19`. This branch is the follow-up, open as a pull request and NOT merged: that instruction
covered only those two.

It retires five decision records about the harness that left, corrects ten product statements in
`optimizing-context` and `building-skills` against the Claude Code docs as read on 22-Nov, and
stops the budget guard capping the decisions README, which CI never capped.

Decided: both skills stay (their only numbers, in `benchmarks/2026-10-12-g8-shortfall/`, lean
positive with intervals that include zero).
The review template stays: its findings on #326, #332, #334 were acted on.

Checking the two repos together (repeat after either changes): install all four plugins into a
scratch `CLAUDE_CONFIG_DIR` whose path has a space; start `claude -p --output-format stream-json
--verbose` and read the `init` event; spawn a helper with no model and confirm
`docs/pdca/gate-hits.txt` gains a line; load each `skills/*/evals/evals.json` through
skill-measure's `bench_skill.load_evals`; run `validate.py` over its `skills/bench`.

## Next candidates, ranked

1. **Product statements the fact-check could not confirm.** `optimizing-context/SKILL.md:31` and
   `references/user-preferences.md` (the "User Preferences" name and precedence),
   `references/subagents.md:84,96-97`, `building-skills/references/validation-rules.md:58`.
   Ten checked statements were wrong, so these are suspect: source each or cut it.
2. **The guards are bash**, so Windows needs Git for Windows; a node rewrite removes that.
3. **`validate.py` runs on Python 3.9 but no check holds it there.**

Also: #337 needs a rebase; `control-narratives` returns only if its re-measure beats bare;
a shell edit bypasses the budget guard, and CI is the catch.

## Waiting on the owner

- Turn `pdca-workflow` on for the account, then try `/pdca-workflow:decide` and `/bench` in the
  desktop Code tab and in Cowork. Neither plugin has been run in the app itself.
- `claude setup-token`: for the #328 re-measure and a verdict on the two unmeasured skills; also
  the `CLAUDE_CODE_OAUTH_TOKEN` secret if the advisory review should return (the old one is
  revoked).
- The scheduled task "one21tools self-improvement loop" is OFF: give it this repository with
  push access, then turn it on.
- Decide: ADR 0024 against the sunk-cost ruling; where frozen benchmark evidence lives (22 MB);
  #338 item 3; whether the 90% pause rule also covers the weekly limit.
