---
name: retrospect
description: Use when wrapping up shipped work or before opening a PR. Derives at least 2 routed process improvements from git history plus this session's friction, then applies or escalates each. Explicit-invoke only; never auto-fire.
disable-model-invocation: true
---

# /retrospect — automate the PDCA Act loop

Make the process better after shipping. The process half of the feedback system (the product
half is `/decide` on user feedback). Explicit-invoke only: it spends an agent and edits
process docs, so it must never auto-fire. Run it on this branch before opening the PR, so
improvements land in the still-open PR.

Arguments (optional): $ARGUMENTS = the git range or scope (e.g. `main..HEAD`, a PR number).
Default: `main..HEAD` (this branch's work).

Run this loop:

1. **Scope.** Resolve the range. `git log --oneline <range>` for the commit set.
2. **Git signal.** Surface the rework/waste signals for the `retrospect` agent: fix-of-a-fix
   commits, reverts, a file touched repeatedly, a Sacred file (named in CLAUDE.md) touched
   without its paired test, ADR/tracker drift. (`git log -p <range>` as needed.)
3. **Analyze.** Spawn the `retrospect` agent on the range. It owns the git/code analysis and the
   routing rules — don't restate them.
4. **Add session friction.** YOU (in the main conversation, which the isolated agent cannot see)
   list this session's friction — every user correction, wrong guess, or rework — and hand it to
   the agent. This is the input the agent structurally cannot gather itself.
5. **Curate.** Dedupe; keep only systemic improvements (would recur), at least 2,
   cite-or-silence — never pad to a count. If under two are real, say so.
6. **Route + act.** Route each improvement to its lowest home per the agent's analysis (it owns the
   routing rules). The agent's findings are advice — independently verify each against the repo and
   muda-assess whether the fix beats its cost before applying (a sub-agent's "apply directly" is a
   recommendation, not a command); then apply the cheap, verified, non-judgment ones in this run. If
   an improvement is a judgment call (cost/scope/policy trade-off), open `/decide` and let the PM
   record an ADR — do not decide it here.
7. **Record.** Edit each rule at its home in the same run; do NOT accumulate a "Learned"
   changelog (git history + any ADR are the record of why).

Commit the doc/rule edits. If a rule change implies a code/test change, run the project's test +
build (per CLAUDE.md) before committing.
