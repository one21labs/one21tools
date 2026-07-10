---
id: 0030
title: "PR-body Retrospective line + CI presence gate replace silent skipped-retrospect"
status: accepted
summary: "A skipped pre-PR /retrospect is invisible either way it happens — plugin not installed (web) or merge-as-you-go pressure. Require a PR-body line `Retrospective: run | unavailable | skipped-<reason>` (sanctioning `skipped-batch:<link>`), enforced for PRESENCE (not truth) by a tested CI gate so an omitted line fails instead of passing silently. Reject a size floor: invites tier-shopping."
---

# 0030 — PR-body Retrospective line + CI presence gate replace silent skipped-retrospect

- Date: 2026-07-09
- Owner: PM
- Panel: session-operator + lean-process-engineer (identical fix; unanimity checked, see Justification). Red-team pass folded in (findings 1-3).
- Context: issue #34 names two triggers for a skipped pre-PR `/retrospect` going unnoticed. (a) Plugin not installed in web sessions — ADR 0022 switched to a directory source, but its own REOPEN-IF (a web session confirming `/retrospect` loads) is still open (`0022-web-plugin-directory-source.md` has no `## Act`). (b) Merge-as-you-go pressure — 2026-07-09 skipped `/retrospect` 3x on small PRs, debt paid by one batch retrospect; later PRs wrote ad-hoc "skipped-batch" lines with no sanctioned format. CLAUDE.md:56 today only says "Run `/retrospect` before opening" — no artifact records whether it happened, so a skip is silent.

## Decision
1. Require a PR-body line at CLAUDE.md:56: `Retrospective: run | unavailable | skipped-<reason>`. PR body sections become Purpose / Changes / Testing / Deferred / Retrospective.
2. Sanction batch retrospect as a `<reason>` value: `skipped-batch:<link>` pointing at the PR/commit whose batch retrospect covers this PR. No separate size-floor rule.
3. Reject a bare "PR too small, skip" floor. "Tiny" is not decidable in the moment — an agent under trigger (b)'s pressure tier-shops every PR into "tiny." The `skipped-<reason>` string covers this via `skipped-batch` or a stated reason.
4. Enforce PRESENCE now (not truth): a tested `scripts/check-pr-body.mjs` wired into `gates.yml` on `pull_request` fails a PR whose body lacks a line matching `Retrospective: (run|unavailable|skipped-\S+)`. No script can confirm a retrospect actually ran (that stays self-attested); the gate closes the omission-is-silence hole, since an omitted line was the original bug.

## Justification
Cost is one CLAUDE.md line plus a one-regex tested gate (advisors: effort low, risk low, value high). 0030 elects a fallback ADR 0022's REOPEN-IF lists — on independent grounds, not because 0022's trigger fired: 0022 names TWO conditional fallbacks (expose skills as `.claude/skills/` OR the PR-body line), gated behind an unfired web trigger; trigger (b) is plugin-agnostic and warrants the line now. Trigger (a) closes via the ALWAYS-LOADED CLAUDE.md rule (it loads even when the plugin, and its reminder hook, do not), so the author writes `unavailable` from the rule, not a nudge. Without the presence gate the mechanism has no teeth: an author under pressure omits the line = silence = the very bug this ADR closes (a false `run` is at least a disclosed lie; an omission is not). The gate makes omission fail CI (poka-yoke), consistent with the corpus's tested-`.mjs` gates and CLAUDE.md:41 — so the regex lives in a tested script, not an untested inline `grep`.
Unanimity check: convergence, which `advise` flags as a possible mis-scope signal. Two reframes weighed and rejected (see below): deleting the rule, and a blocking hook that runs `/retrospect` pre-merge. The presence check is the honest middle — gate the artifact's presence, never the retrospect's truth; convergence tracked the real minimal fix.

## Assumptions
- [checkable] `scripts/check-pr-body.mjs`'s predicate accepts `run` / `unavailable` / `skipped-<reason>` and rejects a missing or bare-`skipped` line — owner: gate; `scripts/check-pr-body.test.mjs` via `node --test scripts/*.test.mjs`.
- [checkable-doc] ADR 0022's REOPEN-IF lists the PR-body line as one of TWO conditional fallbacks gated behind an unfired web trigger (`docs/decisions/0022-web-plugin-directory-source.md`, Assumptions) — 0030 elects it on trigger (b)'s independent grounds, not as 0022's settled or sole fallback.
- [verified] the reminder hook fires after `gh pr create` in CLI sessions ONLY (`pdca-workflow/hooks/retrospect-reminder.sh:16-18`); it ships inside the plugin, so in a web session where the plugin does not load the hook is absent too — trigger (a)'s `unavailable` comes from the always-loaded CLAUDE.md rule, not the hook.
- [unverifiable] WEAKEST: an author writes an HONEST value rather than a false `run` — the gate checks PRESENCE, not truth. REOPEN-IF a PR shows `Retrospective: run` with no retrospect artifact/commit on its branch -> escalate to a truth audit (PR-template checklist or manual spot-check).

## Rejected alternatives
- Bare size floor ("skip if tiny") — not decidable in the moment; invites tier-shopping.
- Checkable-metric floor (diff line count) as its own rule — not what the evidence asked (both triggers were tooling/pressure, not size); `skipped-batch` already subsumes it.
- Delete the retrospect rule — it is the skill-improvement loop's forcing function.
- Blocking automation (a hook running `/retrospect`) — gates an LLM judgment call with no tested decision logic.

## Revisit triggers
- Presence gate now fireable; a `Retrospective: run` with no branch artifact -> the REOPEN-IF above (truth audit).
- ADR 0022's REOPEN-IF fires (web still lacks `/retrospect`) -> confirm authors hit the always-loaded rule and write `unavailable` rather than omitting the line.
- gates.yml runs on `pull_request` default types (no `edited`); a body-only fix after the last commit needs a re-run -> add `types: [edited]` if that recurs.
