---
id: 0081
title: "Mitigate pressure-narrowing at failure points: standing session-close retrospect (amends 0030) + the two-why check"
status: accepted
summary: "At the moment of failure, goal pressure narrows diagnosis to 'what makes this pass', and a self-attributed rule violation terminates the why-chain. Mitigation: /retrospect becomes the standing session-close DEFAULT with mechanically recorded compliance (SessionEnd hook + Retrospect-Run token, review /decide at 10 sessions). Every gate/CI/verifier failure gets the two-why check. Records the prevention-instrument doctrine from the 0030 post-mortem."
---

# 0081 — pressure-narrowing mitigation

- Date: 2026-07-19
- Context: the PR #251 cap failure was self-attributed ("didn't measure first") and fixed as an
  instance; the CLASS defect (`budget-edit-guard.sh` never covered the validate.py file class
  while `doc-budgets.md` claimed it did) surfaced only when a forced retrospect read the same
  friction as data (#255). A judgment-gated reflection step fails precisely when needed, because
  the gating judgment is the impaired one.

## Decision
**(a) Session-close retrospect is STANDING (amends ADR 0030 in place).** The per-PR ritual stays
dead; on-demand stays available; session close becomes a defined trigger. Closeout mode (home:
`retrospect/SKILL.md`): scope = everything shipped since session start; the friction hand-off is a
MANDATORY enumerated checklist (corrections, wrong guesses, rework, permission denials, CI
failures). An EMPTY finding list is a valid result; findings land as diffs/issues/ADRs, never
assurance lines.

**(b) The two-why check at every failure point.** Before committing the fix for any gate, CI, or
verifier failure, answer: (1) instance or class? (2) which detection-ladder rung (ADR 0047) should
have caught this earlier, and why didn't it? "Operator error" is NEVER a terminal answer. Home:
CLAUDE.md Muda block — an instruct-rung discipline, not claimed as a forcing function; recurring
unanswered failures escalate the rung.

**(c) Prevention-instrument doctrine (the 0030 post-mortem, recorded so the corpus remembers):**
(i) separate a rotten FORM from its FUNCTION before cutting; (ii) a prevention instrument is
valued by the expected cost of the misses it catches, NOT per-run yield; (iii) cutting a detection
instrument requires a revisit trigger riding an evidence stream INDEPENDENT of that instrument.

**(d) Measured compliance + pre-registered review.** `.claude/hooks/session-end-log.sh` appends
`session-end` to `session-log.txt`, so a SKIPPED closeout is a countable miss. An adopted finding
carries the literal `Retrospect-Run:` token. Series (readout FIRST, no band — 0080's discipline):
adopted artifacts / session-ends. Pre-registered REVIEW at 10 `session-end` lines: a /decide
records keep / demote / mint-band from the readout. Gaming direction is safe: under-logging lowers
measured compliance, biasing toward demotion, never away.

## Justification
Same countermeasure family Toyota chose for the same failure mode in humans: a mandatory default
at the moment judgment is impaired. First forced run went 2-for-2 adopted (#255, this ADR).

## Assumptions
- [unverifiable] WEAKEST — the standing trigger's worth rides on closeout yield persisting past
  the novelty period; the 2-for-2 first run may be a backlog effect. REOPEN-IF: the (d) 10-session
  review, its evidence stream independent of the practice surviving.
- [checkable] the SessionEnd hook logs exactly one boundary line per end. result: vacuous — suite
  green, hook shipped 644, never ran; fixed + canary-guarded in #276 (ADR 0086).
- [verified] the failure mode reproduced in-session: fixed as an instance while the class gap sat
  in `budget-edit-guard.sh` vs `doc-budgets.md`, found only by the forced retrospect (#255).

## Rejected alternatives
- Keep judgment-gated on-demand only — the gate is the impaired judgment.
- Restore the per-PR ritual — 0030's green-line pathology was real; the form stays dead.
- Auto-fire via hook — hooks cannot spawn agents; silent auto-spend violates ADR 0016.
- Mint the 0.5/run band now — n=1, no variance, no exposure story.

## Revisit triggers
- The (d) 10-session review -> a /decide records keep / demote / mint-band.
- The session-end series shows skipped closeouts recurring -> promote the trigger one rung.
- A defect class ships that BOTH checks missed -> the mitigation is insufficient; /decide next.
