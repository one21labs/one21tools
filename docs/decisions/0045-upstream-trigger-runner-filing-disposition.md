---
id: 0045
title: "Keep the upstream trigger-runner filing open, narrowed to the one uncovered fix"
status: accepted
tier: lite
summary: "Disposition of #94: narrowed to the one uncovered fix, both drafts posted in-issue. Superseded 2026-07-11 — owner declined the upstream posting; #94 closed not-planned. ADR 0033's revisit trigger (upstream lands the fixes -> re-diff, consider un-vendoring) still watches independently."
---

# 0045 — upstream trigger-runner filing disposition

- Decision: superseded 2026-07-11. #94 (whether to keep open a narrowed upstream filing for the one uncovered vendored fix, stdin-DEVNULL) closed as not-planned — the owner declined the upstream posting. Both drafts (a stdin-DEVNULL PR and a corroborating comment on open PR #1323) remain in the issue for reference; nothing posted upstream.
- Why: base-rate ~0 merges across ~10 open community PRs in the area discounted new-filing value to mostly reputational; the owner's direct call ended the open question.
- Rejected: file the full 4-fix patch upstream (duplicates open PR #1323, reopens a contested timeout design); rely solely on ADR 0033's watch with no drafted fallback (forfeits the cheap draft-now option — moot once posting was declined).
- Reopen-if: ADR 0033's own revisit trigger fires (upstream lands the fixes -> re-diff, consider un-vendoring) — independent of this disposition and still watching.
- Enforced: `docs/decisions/0033-vendor-trigger-runner.md`'s revisit trigger; issue #94 (closed not-planned).
