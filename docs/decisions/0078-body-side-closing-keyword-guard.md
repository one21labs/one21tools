---
id: 0078
title: "check-pr-body also denies body-side closing keywords that contradict a Partial: line"
status: accepted
tier: lite
summary: "Amends ADR 0054: the gate now denies `Closes #N` (any closing keyword) in the PR BODY when the same body declares `Partial: #N` — GitHub reads body keywords on merge and auto-closes the issue, so the contradiction is exactly as decidable as the title-side case 0054 already denies. Observed once (PR #205 branch, caught by a human); filed as #213, which pre-authorized won't-fix but the fix is ~10 lines on an existing tested surface. Fences/comments stripped first, so examples never deny. Closes #213."
---

# 0078 — body-side closing-keyword guard

- Decision: `scripts/check-pr-body.mjs` gains `bodyClosesDeclaredPartial(body)` (body-closes
  intersect body-partials), wired beside the 0054 title check; unit-tested in the sibling
  test file per the Never rule. A body closing keyword WITHOUT a Partial line still passes —
  same undecidable-intent boundary as 0054 (ADR 0047 precondition ii).
- Why: the residual class was observed in the wild and the guard's whole surface (grammar
  regex, fence stripping, Partial parsing) already exists and is tested — extension cost is
  near zero, and the mis-close it prevents silently lands unresolved work as "done".
- Enforced: gates.yml runs check-pr-body on every PR; decision logic in check-pr-body.test.mjs.
