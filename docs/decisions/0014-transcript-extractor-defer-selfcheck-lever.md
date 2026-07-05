---
id: 0014
title: "Transcript extractor for /retrospect: precondition unmet — defer; add an orchestrator non-git-visible self-check"
status: accepted
summary: "0007's feasibility trigger fired; the CHECK ran, precondition FAILED — transcript_path is documented but the JSONL schema is reverse-engineered/unversioned, type:user != human-typed, a cheap read needs a shipped tag-aware parser (jq absent), attribution is line-level cross-file. Grep-only is infeasible; the feasible parser ships secrets/schema-drift liability + reopens 0006. REJECT the extractor now; ADOPT the cheaper lever (retrospect SKILL.md step-4 non-git-visible self-check); RE-DEFER behind a sharpened precondition. 0006's sonnet tier survives; 0007 is rationalized in place (stale triggers -> 0014's precondition + an Act pivot)."
---

# 0014 — transcript extractor: precondition unmet, defer; add an orchestrator self-check

- Date: 2026-07-04
- Owner: PM
- Panel: opposing counsel (EXTRACTOR / STATUS-QUO) + 1 neutral empirical channel lens arbitrating on the real JSONL. verifier + red-team next. Reopens 0007 (0007:36); touches 0006.
- Context: 0007 deferred an independent transcript-extractor behind a trigger (0007:36) — build only if a "clean, portable, low-cost raw-transcript channel" exists. The trigger fired (harness review). Open call: does it exist; if not, what captures 0007's residual non-git-visible friction?

## Decision
1. **REJECT the extractor as specified — precondition NOT met.** The neutral lens refutes the grep-only premise on the real transcripts: transcript_path is documented BUT the JSONL schema is reverse-engineered + unversioned; type:"user" != human-typed (~12 keystrokes in 142 turns -> naive grep = ~15.6K-token noise); the cheap ~330-token read needs a TAG-AWARE parser (jq absent -> a shipped script); attribution is LINE-level cross-file (uuid-deduped; "pick the file" doesn't exist — one file spans 7 branches). So grep-only is infeasible; the feasible build is a shipped, secrets-handling, schema-drifting parser that reopens 0006.
2. **ADOPT the cheaper lever (STATUS-QUO).** Tighten retrospect `SKILL.md` step 4: the orchestrator marks each perceived friction git-visible?, then runs a one-line self-check — "did the user correct anything NOT reflected in a commit?" Poka-yoke (prevent > detect): the orchestrator PERCEIVES the non-git-visible class at authoring time — the residual 0007 named — at zero shipped surface. Home: `SKILL.md` step 4 (companion to 0007's step-4/5 edits + the git cross-check).
3. **RE-DEFER with a sharpened, testable precondition** (replaces 0007's vaguer "clean, portable, low-cost"): re-fire only when Claude Code ships a DOCUMENTED, VERSIONED transcript schema OR a transcript-query API AND a per-message->commit attribution primitive.
4. **0007: rationalized in place** (its Decision stands — reject transcript-as-default, git cross-check primary). This PR rewrites 0007's stale triggers (0007:36-37,:25 — still promising the OLD loose channel + "escalate to the extractor", a build rejected here) to 0014's sharpened precondition, and appends one `## Act` `[pivot]` line (char budget in the adr-lint assumption below).
5. **0006's sonnet tier SURVIVES** unchanged: no extractor = no new input class to the retrospect agent, no auto-apply wiring; the lever is orchestrator-side (`SKILL.md`), touches no agent model. 0006's REOPEN-IF does not fire.

## Justification
The extractor's value is an INDEPENDENT witness — but the only feasible build is a shipped parser (secrets + unversioned schema, reopening 0006): HIGH surface, for ONE case that was itself git-visible (caught by 0007's cross-check). The step-4 self-check captures most of that value at zero surface — cheap-now beats build-expensive until the channel is clean.

## Assumptions
- [checkable] **WEAKEST** — the step-4 self-check meaningfully catches non-git-visible friction the git cross-check misses. It nudges the SAME author to introspect — a targeted prompt beats silence, but does NOT sever author-from-curator (the extractor's full cure), so it is no structural guarantee. TEST (owner: verifier): the step-4 edit names the git-visible tag + the self-check question, feeds step 5, cannot pad findings. — result: pending.
- [checkable] the lever is orchestrator-side `SKILL.md` only — no script/CI, no agent-model change; adr-lint stays green, incl. 0007 under its 6,000 cap (5,975 now): the L36 rewrite + L25/L37 trims free ~118 chars, offsetting the ~96-char `[pivot]` = net -22, so 0007 -> ~5,953 (B2). 0006 untripped. — owner: verifier.
- [contradiction] 0007's live triggers (0007:36-37,:25) contradict this Decision — pointing at the rejected extractor + old loose condition. FIXED this PR: rewrite them to 0014's precondition (Decision 4). — PM-verified vs 0007.
- [unverifiable] no clean+versioned transcript channel exists today. — REOPEN-IF: Claude Code ships a documented/versioned transcript schema or a transcript-query API -> re-run the extractor call (re-opens 0006).

## Rejected alternatives
- **The extractor, either form** — grep-only is refuted empirically; the feasible parser is a process-gating script shipped to every consumer (needs a test, CLAUDE.md Never) handling a secrets class + unversioned schema — disproportionate to one git-visible anecdote, and reopens 0006.
- **Do nothing (pure hold)** — leaves 0007's named non-git-visible residual unaddressed; the step-4 lever closes most of it for free.

## Revisit triggers
- A USER later surfaces a non-git-visible retro miss the step-4 self-check should have caught (the only EXTERNAL observer — the author can't self-observe the miss, which is why the extractor's independent witness would be the full cure) -> lever insufficient; re-weigh the extractor.
- retrospect wired to auto-apply a finding, or 0006's A/B lands sonnet-inadequate -> re-evaluate lever + tier together.
