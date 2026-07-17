---
id: 0072
title: "three-dot-warn fires on git diff only"
status: accepted
tier: lite
summary: "ADR 0047(c)'s warn hook matched log, diff, and rev-list, but the tip-to-tip trap is diff-specific: log/rev-list two-dot is the CORRECT commits-ahead query (three-dot = symmetric difference, worse). Hook now fires on git diff only. From PR #217's retrospective."
---

# 0072 — three-dot-warn scoped to git diff

- Decision: `.claude/hooks/three-dot-warn.sh` fires only when `git diff` runs a two-dot range
  against main; `log`/`rev-list` are dropped. Tests flipped (log/rev-list two-dot now assert
  silent); `retrospect.md`'s git-signal line states the per-subcommand forms.
- Why: PR #217's retrospective reproduced the false fire live (`git log origin/main..HEAD`,
  the idiomatic PR-commit listing, warned + counted). ADR 0047(c)'s trigger reads "counted log
  clean -> promote to deny" — promoted as-is it would DENY correct `git log` usage. The warn's
  rationale (tip-to-tip preview) only describes diff. Pre-fix `two-dot-main` log entries in
  docs/pdca/session-log.txt are discounted when reading the promotion window.
- Enforced: `.claude/hooks/three-dot-warn.sh` + `test-three-dot-warn.sh` (the silent cases
  fail on the old predicate); 0047(c)'s deny promotion now reads on diff fires only.
