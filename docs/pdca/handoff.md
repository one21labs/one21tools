# Handoff

Written 21-Nov-2026 on `claude/brave-pasteur-4ho96t` (PR #339), on top of `f5773bd`. Rewrite this
file whole each turn (`pdca-workflow/commands/improve.md`, step 8). Where it disagrees with git
or the tracker, they win.

Goal (`README.md`): quality output, autonomously, judged as the person receiving it.

## Measures

| Measure | Baseline `d4bcbc2` | Now | Target |
|---|---|---|---|
| Shipped skills with a promoted "helps" verdict | 1 of 5 | 1 of 5 | 5 of 5, none below bare |
| Known user-facing defects on `main` | 4 | 4 (1 once #339 merges) | 0 |
| Internal record or issue numbers in shipped, model-loaded text | 37 | 0 | 0 |
| Shipped guidance, bytes | 218,629 | 222,384 | no larger than baseline |
| Gate and hook code with tests, bytes | 344,073 | 345,621 | smaller than baseline |
| `CLAUDE.md` chars against its 6,000 cap | 5,637 | 5,998 | headroom of 300 |

How to read them: verdicts from the README "Measured state" table; cites with
`grep -rnE 'ADRs? [0-9]{4}|#[0-9]{2,3}\b'` over `skills/*/SKILL.md`, `skills/*/references`,
`pdca-workflow/{skills,agents,commands}`; bytes with `wc -c` over the same set, and over
`scripts/*.mjs`, `pdca-workflow/{scripts,hooks}`, `.claude/hooks`, `validate*.py`, `gates.yml`.

The two byte measures moved the wrong way this turn: the Workflow guard, the role-spawn rule
and the loop command added more than the cuts removed.

## Shipped this turn

PR #339: the ready half of #337; hook paths quoted; the model guard covers Workflow scripts; a
lost agent is never a result; shipped text cleaned of private record numbers; one gate deleted;
the handoff file allowed; this loop.

## Next candidates, ranked

1. **`control-narratives` still ships text that scored below the bare model** (#328: pooled
   -0.103, interval [-0.191, -0.016]). A defect users receive. Revision 2 waits on #337, which
   waits on the owner's `claude setup-token`. If that has not moved, propose removing the skill
   from the marketplace until it is measured.
2. **The advisory review has not posted on #339.** Run 44874369631 ended after one turn, no
   model use and no cost (the account was at 92% of its 5-hour limit minutes earlier). The next
   run, 44874897554, finished green and the PR still has no review comment. Green and silent is
   a guard that does not fire: read that run's `claude-review-execution-log` artifact for the
   denied or missing `gh pr comment`.
3. **`dev-skills` and `engineering-skills` each ship all five skill folders and every
   `evals/`**, because both use `source: ./skills`. Seen in an account-synced install. Text
   shipped that earns nothing; the fix moves folders and strands frozen benchmark cites, so it
   needs the owner's call on `check-relocated-paths` first.

Also true, unranked: `CLAUDE.md` sits at its cap and needs a whole-file cut; about 120 comments
in shipped hooks and scripts still cite internal records.

## Waiting on the owner

- Merge #339, then #337 needs a rebase onto it.
- Turn `pdca-workflow` on for the account (desktop app: Customize, Plugins). Until then no
  cloud session loads it, and nobody has confirmed its agents and guards load there.
- `claude setup-token`, for the #328 re-measure.
- The scheduled task "one21tools self-improvement loop" (daily 10:41 UTC) exists but is turned
  OFF: a test firing got 403 on this repo, because a task created from a session carries no
  repository. Attach `one21labs/one21tools` with push access to it in the scheduled-tasks
  settings, then turn it on. Until then the loop runs only when someone types
  `/pdca-workflow:improve`.
- Decide: delete `check-relocated-paths` before its own 12-month condition; where frozen
  benchmark evidence lives; whether guards are copied into adopting repos (#338 item 3); whether
  the 90% pause rule also covers the weekly limit (83% at 06:11 UTC, resets Sun 22-Nov 18:00 UTC).
