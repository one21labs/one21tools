---
id: 0030
title: "PR-body Retrospective line replaces silent skipped-retrospect"
status: accepted
summary: "A skipped pre-PR /retrospect is currently invisible either way it happens — plugin not installed (remote/web) or merge-as-you-go pressure (3 skips on 2026-07-09, debt paid by one batch retrospect). Add a required PR-body line, `Retrospective: run | unavailable | skipped-<reason>`, sanctioning `skipped-batch:<link>` as a named reason. Reject a size floor: not decidable in the moment, invites tier-shopping. This is ADR 0022's own named fallback, not new machinery."
---

# 0030 — PR-body Retrospective line replaces silent skipped-retrospect

- Date: 2026-07-09
- Owner: PM
- Panel: session-operator + lean-process-engineer (both advise the identical fix; unanimity checked against a reframe, see Justification).
- Context: issue #34 names two triggers for a skipped pre-PR `/retrospect` going unnoticed. (a) Plugin not installed in remote/web sessions — ADR 0022 switched the marketplace source to a directory source, but its own REOPEN-IF (a fresh web session confirming `/retrospect` loads) is still open; `docs/decisions/0022-web-plugin-directory-source.md` carries no `## Act`. (b) Merge-as-you-go pressure — 2026-07-09 skipped `/retrospect` 3x on small PRs, debt paid by one batch retrospect; later small PRs then wrote ad-hoc "Retrospective: skipped-batch" body lines with no sanctioned format. CLAUDE.md:56 today only says "Run `/retrospect` on the branch before opening it" — no artifact records whether that happened, so a skip (for either reason) is silent.

## Decision
1. Add a required PR-body line at CLAUDE.md:56: `Retrospective: run | unavailable | skipped-<reason>`. PR body sections become Purpose / Changes / Testing / Deferred / Retrospective.
2. Sanction batch retrospect as a named `<reason>` value: `skipped-batch:<link>` pointing at the PR/commit holding the batch retrospect that covers this PR. No separate size-floor rule.
3. Reject a bare "PR is too small, skip retrospect" size floor. "Tiny" is not decidable in the moment — an agent under the same merge-as-you-go pressure that caused trigger (b) would tier-shop every PR into "tiny." The `skipped-<reason>` string already covers this case (`skipped-batch`, or a stated reason) without a second rule.

## Justification
Cost is one CLAUDE.md line (both advisors: effort trivial/low, risk low, value high/medium). Not new machinery: ADR 0022's own `[unverifiable]` assumption already names "the PR-body-visibility line" as its fallback if web auto-install doesn't hold (docs/decisions/0022-web-plugin-directory-source.md, Assumptions) — 0030 exercises that named fallback now both triggers have evidence, rather than inventing a third mechanism. Closes trigger (a) regardless of whether 0022's fix holds in a given session: `unavailable` is the honest string an author writes when the plugin didn't load, making the failure visible instead of silently absent. Closes trigger (b) because a false `run` is a disclosed lie an author must actively write, not a default silence.
Unanimity check: the panel converged, which `advise` flags as a possible mis-scope signal. Considered two reframes: (i) delete the retrospect rule — rejected, it is the skill-improvement loop's forcing function, not ceremony; (ii) fully automate via a blocking hook running `/retrospect` pre-merge — rejected, `/retrospect` is an LLM judgment call over git history + friction, not a deterministic gate. The existing reminder hook is deliberately non-blocking for this reason (`pdca-workflow/hooks/retrospect-reminder.sh:3,16-18`). A blocking version is new, unproven gating logic, out of scope for a visibility issue (CLAUDE.md:41 bars an untested gating script). Neither reframe beats the self-attested line; convergence tracked the real minimal fix, not a missed alternative.

## Assumptions
- [checkable-doc] ADR 0022's REOPEN-IF names the PR-body line as its own fallback (`docs/decisions/0022-web-plugin-directory-source.md`, Assumptions section) — this ADR fulfills that fallback rather than contradicting or duplicating it.
- [verified] A non-blocking reminder hook already fires after `gh pr create` (`pdca-workflow/hooks/retrospect-reminder.sh:16-18`) — the gap this ADR closes is the missing visible artifact, not missing tooling.
- [unverifiable] WEAKEST: authors write an honest `skipped-<reason>` / `unavailable` rather than a false `run` — no script can verify a retrospect actually happened without re-running it, so the line is self-attested, not gated. REOPEN-IF a PR is found with `Retrospective: run` but no retrospect artifact/commit on that branch -> escalate to a template checklist or a CI check for the line's mere presence (not its truth).

## Rejected alternatives
- Bare size floor ("skip if PR is tiny") — not decidable in the moment; invites tier-shopping under the same pressure that caused trigger (b).
- Checkable-metric floor (e.g. diff line count) as its own rule — not requested by the evidence (both triggers were tooling/pressure, not PR size); would add a second rule the reason-string already subsumes via `skipped-batch`.
- Delete the retrospect rule — it is the skill-improvement loop's forcing function, not ceremony.
- Blocking automation (a hook that runs `/retrospect` itself pre-merge) — turns an advisory nudge into a gate on an LLM judgment call with no tested decision logic; over-scope for a visibility-only issue.

## Revisit triggers
- A PR is found with `Retrospective: run` but no retrospect artifact on the branch -> the REOPEN-IF above.
- ADR 0022's own REOPEN-IF fires (a fresh web session still lacks `/retrospect`) -> re-confirm authors actually see and can write `unavailable` rather than hitting a silent "Unknown command" failure.
