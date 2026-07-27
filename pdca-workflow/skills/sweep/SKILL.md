---
name: sweep
description: Use when a skill, plugin, or codebase needs auditing until it is clean rather than audited once. Runs independent rounds until consecutive rounds find nothing new or a stated cap is hit, and reports which of the two happened.
---

# /sweep — iterate an audit until it converges, or say plainly that it did not

One pass finds the defects it happened to look for, and each fix can introduce its own. This
loops both until the finding rate reaches zero, and refuses to call that outcome reached when
what actually ran out was rounds.

$ARGUMENTS = the target, then the cap: `pdca-workflow --max 6`. Omit it and sweep-state.mjs
applies its own default — that constant is the one home, so this file does not restate it.

## Before round 1

1. **Fix the surface and write it down** — the files, dirs, and question classes in scope. A
   later round that finds less because it looked at less is indistinguishable from a clean one,
   and drifting inward is the cheapest way to fake convergence.
2. **Pick the finding-id scheme**: one stable slug per distinct defect (`hook-lib-missing-test`),
   assigned when the defect is first seen and never re-minted. Round 4 has to be able to tell a
   repeat from something new, and only the id does that.
3. **Open the round log**, one JSON object per line, in the project's own log dir
   (`docs/pdca/sweep-<target>-<YYYY-MM-DD>.jsonl` here).

## Each round

1. **Sweep the whole declared surface of the CURRENT tree** — above all the parts the last
   round's fixes touched. Fix-induced defects are the dominant class after round 1, so a round
   that only re-checks what it changed last is the one that misses them.
2. **Lanes, not one look.** Spawn independent lanes with different questions (correctness,
   staleness, dead references, contract drift) rather than one general pass — a single lane
   returns its own priors. Any finding ABOUT this loop or the tooling running it needs a
   foreign-vendor lane, not a sibling: `node "${CLAUDE_PLUGIN_ROOT}/scripts/crosscheck.mjs"`
   (ADR 0093 owns the class and the FRAME-UNCHECKED result).
3. **Verify each candidate against the real tree before it counts.** An unverified finding is
   not a finding: it inflates the round, and the fix it triggers is pure new risk.
4. **Fix what is cheap and verified; open an issue for the rest** (ADR 0021 — deferred work
   tracks in issues, never in a handoff file). Then re-run the project's deterministic gates: a
   fix that breaks a gate is next round's finding, not this round's success.
5. **Append the round line** — `{"round": N, "ids": ["slug-a"], "xfam": "<model that answered>"}`,
   verified findings only. A round that found nothing still gets a line with an empty array; that
   line IS the evidence of convergence, and a skipped one silently shortens the quiet tail.
   `xfam` names the cross-lineage model, read back from the lane (`crosscheck.mjs`), and it must
   appear on a round INSIDE the quiet tail — omit it and the verdict is FRAME-UNCHECKED, not CLEAN.
   Documenting the shape without it produced exactly that dead end.
6. **Ask the script for the verdict — never decide it in prose:**
   `node "${CLAUDE_PLUGIN_ROOT}/scripts/sweep-state.mjs" <log> --max <N>`. It owns the stopping
   states, their exact meaning, and the exit code for each; its header is the one home for all of
   that, and it prints the reason with the verdict.

## Reporting

Relay the script's verdict and its reason line as written — do not paraphrase a stopping state
into a warmer one, which is the whole failure this skill exists to prevent.

Add what the script cannot see: the declared surface, and the findings per round with which round
each was found in. The shape of that curve is the evidence. A sweep whose findings are still
climbing at the last round has not told you the code is nearly clean; it has told you the cap was
too low.
