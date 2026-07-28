---
id: 0091
title: "gate-pipe-guard.sh deleted, not retrofitted: scoped by a three-prong test, not blanket undecided-cleanup"
status: accepted
tier: lite
summary: "gate-pipe-guard.sh (both copies) + tests deleted, not retrofitted — no ADR ever decided its predicate, yet it was re-cited as settled authority (mention-laundering). Scoped by a three-prong test so it can never be cited to delete adr-lint.mjs or claude-review.yml."
---

# 0091 — delete-not-retrofit for an undecided BLOCKING guard, scoped narrowly

- Decision: `gate-pipe-guard.sh` (both copies) + tests + hooks/settings registrations stay
  deleted, not retrofitted — a BLOCKING hook with zero ADR ever deciding its predicate, yet
  re-cited as settled authority twice (**mention-laundering**: a mention inherited as a
  decision). **Three-prong test, ALL conjunctive:** (i) BLOCKING; (ii) zero decided predicate
  anywhere; (iii) legitimacy via undisposed re-citation. **Not authorized to delete**
  `adr-lint.mjs` (fails ii — decided: 0088/0087/0067/0020) or `claude-review.yml` (fails i —
  non-blocking). `post-edit-gate.sh` was listed too; it went 2026-07-27
  because CI already ran all it ran (#311), not via this test.
- Why: deciding ABOUT a shipped artifact isn't deciding the question — a blocking artifact
  frames the option toward "keep as built." Premise was wrong too: `pipefail`/`PIPESTATUS`
  don't lose an exit code across a pipe.
- Rejected: retrofit as-built — no decided content to preserve. Delete-all-undecided — most
  audited mechanisms are decided; wrongly reaches adr-lint.mjs.
- Reopen-if: a second BLOCKING, zero-predicate, re-cited mechanism surfaces — apply this path.
  A record cites 0091 to delete adr-lint.mjs or claude-review.yml — invalid on its face. PR#134's pipe-mask hazard recurs — rebuild targets `pipefail`/`PIPESTATUS` first.
- Enforced: deletion is in the tree; `.github/workflows/gates.yml` is the one home for the wired set, so an unwired guard has no invocation.
