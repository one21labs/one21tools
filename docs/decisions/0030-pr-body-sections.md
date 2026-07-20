---
id: 0030
title: "PR body: Purpose / Changes / Testing / Deferred; retrospect trigger (amended by ADR 0081)"
status: accepted
summary: "A PR body carries Purpose / Changes / Testing / Deferred. The per-PR retrospect mandate and its Retrospective: line stay removed (owner rework 2026-07-16, the ceremony cut): per-PR measurements found no quality edge and the ritual's green line manufactured false assurance. Retrospect trigger amended by ADR 0081: session-close standing + on-demand — the per-PR form stays dead. check-pr-body keeps only the ADR 0054 title/Partial contradiction guard."
---

# 0030 — PR body sections; retrospect trigger

- Date: 2026-07-16

Owner decision, recorded directly (2026-07-16); retrospect trigger amended by ADR 0081
(2026-07-19). Enforced homes: `scripts/check-pr-body.mjs` (ADR 0054 guard only),
`.claude/hooks/pr-create-guard.sh` (disclosure + body-file + external target), CLAUDE.md
Shipping + the Muda forcing-functions line (the ADR 0081 closeout step).

- [unverifiable] session-close output (ADR 0081) does not regrow the green-line rot — REOPEN-IF
  a closeout emits findings with no routed artifact (the citing-artifact gap, observable in
  0081 (d)'s readout independent of its keep/demote outcome): that re-opens the FORM question
  here, not just the trigger question there.

## Act (post-ship — 2026-07-19)
- [outcome] on-demand-only retrospects catch what the per-PR ritual caught — violated: the
  budget-edit-guard class gap (#255) stayed unfound until a forced session-close run.
- [pivot] the REOPEN-IF fired (a measured instance, not a hunch); discharged into ADR 0081 —
  session-close becomes the standing trigger, the per-PR form stays dead, and 0081 (c) records
  why this cut over-reached.
