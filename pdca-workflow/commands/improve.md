---
description: Run one turn of the project's self-improvement loop — read the handoff, ship the one change that closes the largest gap to the goal, rewrite the handoff.
argument-hint: [optional focus — an area, a measure, or an issue number]
---

One turn of this project's self-improvement loop. A turn starts cold: its only memory is git, the
tracker, and `docs/pdca/handoff.md`. Focus: $ARGUMENTS — if empty, the measures decide.

1. **Usage first.** Read the account's usage (the `usage-limits` skill where present). At or
   above the project's pause level (CLAUDE.md, Usage; 90% of the 5-hour window if it states
   none): schedule a resume just after the reset and stop. Check again after each large step.
2. **Read state.** `git fetch`; read the handoff, the open PRs with their checks and review
   comments, and the open issues. Where git or the tracker disagree with the handoff, they win.
3. **Finish before starting.** An open PR from an earlier turn comes first: answer its review
   comments, fix its red checks, rebase it. If it is green and only waits on the owner, start
   nothing new — say so in the handoff and stop.
4. **Measure, then ship ONE package.** Run the gates and each measure the handoff names; a
   measure that cannot be read is reported as unread, never estimated. Then run
   `/pdca-workflow:MSH` on the change that most closes the gap to the project's goal, ranked: a
   defect a user receives; a guard that silently does not fire; text a model loads that earns
   nothing; process waste. Try the deletion first.
5. **Close the turn.** `/retrospect` on this turn's range, real findings landed in the same PR.
   Then rewrite the handoff whole, never an append: the date and commit; each measure's
   baseline, last and current reading; what shipped; the next three candidates with the evidence
   that ranks each; what waits on the owner. Leave out anything git or the tracker already holds.
