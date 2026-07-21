---
name: retrospect
description: Use when a session closes (standing, ADR 0081) or when shipped work felt wrong or worth learning from — never as per-PR ritual. Derives routed process improvements from git history plus this session's friction (an empty result is valid), then applies or escalates each. Trigger-bound: fires only at those triggers, never outside them.
---

# /retrospect — automate the PDCA Act loop

Make the process better after shipping. The process half of the feedback system (the product
half is `/decide` on user feedback). Trigger-bound (ADR 0016): it spends an agent and edits
process docs, so it fires ONLY at the two ADR 0081 triggers, never outside them: SESSION CLOSE — standing,
because at the moment of failure goal pressure narrows diagnosis and self-blame terminates
why-chains, so the reflection step cannot be gated on the impaired judgment — and ON DEMAND
while a PR is still open, so findings can land in it. The dead per-PR ritual (ADR 0030) stays
dead: an EMPTY finding list is a valid result; output lands as diffs/issues/ADRs, never a
green reassurance line.

Arguments (optional): $ARGUMENTS = the git range or scope (e.g. `origin/main...HEAD`, a PR number).
Default: `origin/main...HEAD` (this branch's work; three-dot against the remote tip, not stale
local `main`).

**Session-close mode (ADR 0081).** Scope = everything shipped since session start (list the
merged PRs/commits). Step 4's friction hand-off is MANDATORY and enumerated as a checklist —
user corrections, wrong guesses, rework, permission denials, gate/CI failures — each marked
git-visible y/n. Invoke via this skill, not a raw agent spawn: the spawn-log line marks the
run (a raw spawn only lowers 0081's measured compliance — session-end lines are the
denominator). An adopted finding's artifact carries the literal token
`Retrospect-Run: <UTC timestamp of the run's spawn-log line>` (commit trailer or issue-body
line) — 0081's grep-able numerator. Step 2's material includes `docs/pdca/gate-hits.txt`
(the agent's Method reads it).

Run this loop:

1. **Scope.** Resolve the range. `git log --oneline <range>` for the commit set.
2. **Git signal.** Run `git log -p <range>` as needed so the material is ready for the agent; its
   Method owns the specific signal list to look for (including the panel-fire log) — don't restate
   it here.
3. **Analyze.** Fetch, then spawn the `retrospect` agent on the `origin/main...HEAD` range (not
   stale local `main`, which mis-ranges after an upstream squash-merge). It owns the git/code
   analysis and the routing rules — don't restate them.
4. **Add session friction.** YOU (in the main conversation, which the isolated agent cannot see)
   list this session's friction — every DISTINCT user correction, wrong guess, or rework — and hand
   it to the agent. Mark each item git-visible? (yes/no) — the agent can only corroborate the yes
   class. Self-check before handing off: "did the user correct anything not reflected in a
   commit?" — add those items; that class has no other witness (ADR 0014).
   Enumerate each before deduping (the agent dedupes at step 5); do NOT restate
   redundant variants. This is the input the agent structurally cannot gather itself, but it is your
   PERCEPTION only — the agent independently cross-checks it against git (its Method), so a
   git-visible miss is caught, a non-git-visible one is not.
5. **Curate.** Dedupe the enumerated list; drop non-systemic items first (the enumerate-all
   above must not pressure the no-pad rule); keep only systemic improvements (would recur),
   cite-or-silence — as many as are REAL: zero is the expected result of a clean closeout
   (ADR 0081), never pad to a count. If none are real, say so.
6. **Route + act.** Route each improvement to its lowest home per the agent's analysis (it owns the
   routing rules). The agent's findings are advice — independently verify each against the repo and
   muda-assess whether the fix beats its cost before applying (a sub-agent's "apply directly" is a
   recommendation, not a command); then apply the cheap, verified, non-judgment ones in this run (e.g.
   `/simplify`, the Claude Code built-in that owns the reuse/simplification/altitude cleanup pass). If
   an improvement is a judgment call (cost/scope/policy trade-off), open `/decide` and let the PM
   record an ADR — do not decide it here.
7. **Record.** Edit each rule at its home in the same run; do NOT accumulate a "Learned"
   changelog (git history + any ADR are the record of why).

Commit the doc/rule edits. If a rule change implies a code/test change, run the project's test +
build (per CLAUDE.md) before committing.
