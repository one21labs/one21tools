---
id: 0045
title: "Keep the upstream trigger-runner filing open, narrowed to the one uncovered fix"
status: accepted
summary: "Disposition of #94: keep it OPEN, narrowed. Fixes 1+3 and the #104 fallback are already covered by open upstream PR #1323 (corroborating comment may be DRAFTED); stdin-DEVNULL is covered by NO open PR and is independent of #1323 — the one fix worth an upstream PR, drafted now, posting gated only on owner approval (no artificial hold); timeout-as-null is contested (#1298 chose differently), not filed. No new PR without approval; ADR 0033's triggers already watch upstream."
---

# 0045 — Keep the upstream trigger-runner filing open, narrowed to the one uncovered fix

- Date: 2026-07-10
- Owner: PM
- Panel: opposing counsel A (steelman upstream engagement), opposing counsel B (steelman in-repo consolidation), process-economist.
- Context: ADR 0033 vendored skill-creator's run_eval.py with 4 fixes. Verified 2026-07-10: upstream anthropics/skills run_eval.py is unchanged since 2026-02-25 (all 4 defects present); ~10 open community PRs in the area, none merged; open PR #1323 covers vendored fixes 1+3 and the #104 fallback; open PR #1298 covers detection+Windows+workers but chose timeout-as-False-with-warning; NO open PR covers stdin-DEVNULL. All external posting stays owner-gated (CLAUDE.md external-publication rule).

## Decision
Keep #94 OPEN, narrowed. The split is not file-everything vs close — it is covered vs uncovered:
- Fixes 1+3 + the #104 fallback are covered by open PR #1323 → no new filing; a corroborating comment on #1323 may be DRAFTED (owner-gated posting) as low-cost engagement.
- stdin-DEVNULL is covered by NO open PR (a process-hang risk the community hasn't surfaced) and is technically INDEPENDENT of #1323 → it is the one fix worth an upstream PR, DRAFTED now; the only gate on posting is owner approval (no artificial hold-until-#1323 — that coupling controlled nothing).
- timeout-as-null is contested upstream (#1298 chose a different design) → not filed unless it wins a design argument.
No new PR is opened without owner approval. ADR 0033's revisit triggers already watch upstream.
New scope line for #94: "Keep open — narrowed to the single uncovered fix (stdin-DEVNULL): draft an upstream PR for it now plus a corroborating comment on PR #1323; both post only on owner approval (external-publication rule). No dependency between the two."

## Justification
Base-rate ~0 merges discounts any new-PR value to mostly reputational; PR upkeep + owner-approval review is a real cost. But closing forfeits the cheap option to file the ONE uncovered fix (stdin-DEVNULL), and reopening later costs more than a narrowed open issue (which costs nothing — ADR 0033's triggers watch upstream). So: capture the covered value at zero cost (a #1323 comment draft), preserve the uncovered option (a stdin-DEVNULL draft, ready to post on owner approval), pay no PR-upkeep now. The draft has no technical dependency on #1323 — the earlier "hold until #1323" was a false coupling (posting is owner-gated regardless, and stdin-DEVNULL is independent). This is the reframe both counsels' value converges on.

## Assumptions
- [verified] no open PR fixes stdin-DEVNULL; #1323 covers 1+3+#104; #1298 chose timeout-as-False — per the 2026-07-10 re-search in this batch's brief.
- [unverifiable] none of the ~10 open PRs merges soon (base-rate ~0 in the window) — REOPEN-IF #1323 merges (re-diff, un-vendor per ADR 0033) OR upstream ships stdin-DEVNULL (drop the draft).
- [checkable-doc] this doesn't contradict ADR 0033 — verified: 0033's revisit trigger ("if upstream lands the fixes, re-diff and consider un-vendoring") is the reopen mechanism; it hasn't fired (upstream unchanged).

## Rejected alternatives
- File the full 4-fix patch upstream now — duplicates #1323 (fixes 1+3), re-opens a contested design (timeout), pays upkeep against ~0 merge throughput.
- Close #94, rely solely on ADR 0033's trigger (counsel B) — forfeits the cheap file-the-one-uncovered-fix option; reopening later costs more than a narrowed open issue.
- Post anything now without owner approval — barred by CLAUDE.md external-publication rule (drafting only).

## Revisit triggers
- PR #1323 merges → re-diff the vendored copy and un-vendor per ADR 0033 (a separate decision from filing stdin-DEVNULL, which is independent).
- Upstream ships stdin-DEVNULL → close #94, drop the draft.
- Owner approves the drafted text → post the stdin-DEVNULL PR and/or the #1323 comment per the external-publication rule (neither waits on the other).

## Act (post-ship — 2026-07-10)
- [outcome] both drafts posted in #94 (comment + retitle), nothing posted upstream; #94 stays open, owner-gated — verified (PR #131).
- [pivot] red-team O7 removed the hold-until-#1323 coupling before ship.
- [outcome] 2026-07-11: owner declined the upstream posting; #94 closed as not planned (drafts remain in the issue for reference). This supersedes the keep-open disposition; ADR 0033's revisit trigger (upstream lands the fixes → re-diff, consider un-vendoring) still watches upstream independently.
