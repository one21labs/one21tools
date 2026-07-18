---
id: 0077
title: "session-log.txt merges with merge=union"
status: accepted
tier: lite
summary: "docs/pdca/session-log.txt gets a .gitattributes merge=union entry. The hook-appended log (spawn-log.sh, >>) is timestamped, order-independent, and multi-branch — any two branches that both append in a window conflict on rebase/merge (PR #231's rebase reproduced it manually). Union merge concatenates both sides, losing nothing: every consumer reads by timestamp/range, never line position. Closes #232."
---

# 0077 — union-merge the session log

- Decision: `.gitattributes` gains `docs/pdca/session-log.txt merge=union`. No other file
  changes strategy; the existing `* text=auto eol=lf` line stays.
- Why: append-only + tracked + multi-branch = structurally guaranteed conflicts; the poka-yoke
  is telling git the file's actual semantics (an unordered append set) instead of resolving the
  same conflict by hand forever.
- Enforced: the attribute itself; if a future consumer starts depending on line order, that
  consumer is the bug (spawn-log.sh writes self-contained timestamped lines by contract).
