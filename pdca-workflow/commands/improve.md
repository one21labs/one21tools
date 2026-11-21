---
description: Run one turn of the project's self-improvement loop — read the handoff, measure against the goal, ship the one change that closes the largest gap, improve the process, rewrite the handoff.
argument-hint: [optional focus — an area, a measure, or an issue number]
---

One turn of this project's self-improvement loop. A turn starts cold: its only memory is git, the
tracker, and `docs/pdca/handoff.md`. It ends by leaving the next turn better placed than it was.
Run it by hand, or on a schedule (one turn per firing, a fresh session each time).

Focus: $ARGUMENTS — if empty, the measures decide.

1. **Usage first.** Read the account's usage (the `usage-limits` skill where present). At or
   above the project's pause level (CLAUDE.md, Usage; 90% of the 5-hour window if it states
   none): schedule a resume just after the reset and stop. Check again after each large step.
2. **Read state.** `git fetch`; read `docs/pdca/handoff.md`, the open PRs with their checks and
   review comments, and the open issues. The handoff is a pointer, not the truth: it was written
   before git and the tracker moved, so where they disagree with it, they win.
3. **Finish before starting.** An open PR from an earlier turn comes first: answer its review
   comments, fix its red checks, rebase it. If it is green and only waits on the owner, start
   nothing new — record that in the handoff and stop. The loop moves as fast as the owner merges;
   one waiting PR is a decision the owner can make, five are a backlog.
4. **Measure.** Run the project's gates and each measure the handoff names. Record the readings
   beside the last ones. A measure that cannot be read is reported as unread, never estimated.
5. **Pick ONE package** — the change that most closes the gap between the readings and the
   project's goal (CLAUDE.md states it). Rank candidates in this order: a defect a user of the
   product receives; a guard that silently does not fire; text a model loads that earns
   nothing; process waste. Try the deletion first. State in one line why the winner won, and
   name the runner-up without starting it.
6. **Ship it** under the project's standing rules, as `/pdca-workflow:MSH` does: one cohesive
   package, a PR, never a merge. Run the gates before the push.
7. **Improve the process.** Run `/retrospect` on this turn's range. Land its real findings in
   the same PR; zero findings is a valid result.
8. **Rewrite the handoff** — the whole file, never an append — and commit it in the PR:
   - the date and the commit it was written at;
   - each measure: baseline, last reading, this reading;
   - what this turn shipped, in one line, with its PR;
   - the next three candidates, ranked, each with the evidence that ranks it;
   - what is waiting on the owner.
   Leave out anything git or the tracker already holds. A handoff that grows is one that has
   started keeping history; cut it back to what the next turn needs to start.

Close with the plain summary: what shipped, what the measures say, what the owner must do next.
