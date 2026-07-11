---
id: 0049
title: "Defer proactive trigger-testing of the model-invocable primitives; mechanize the reactive trigger with a spawn-log hook"
status: accepted
summary: "Decline proactively TP/FP-testing the three always-loaded pdca descriptions (advise/red-team/verify) — ADR 0016's tight triggers hold and zero misfires are observed. But the primitives emit no git artifact, so 0016's reactive trigger is blind in autonomous mode: mechanize it with a PreToolUse spawn-log hook (rung-2, ADR 0047). When a misfire is seen, run an 8+8 both-arm set for the offending skill on the next benchmark — the should-fire arm guards the false-negative/Wrong-PASS class (0016:13), not only panel-spawn."
---

# 0049 — defer proactive trigger-testing; mechanize 0016's reactive trigger

- Date: 2026-07-10
- Owner: PM
- Panel: `/advise` two-sided (counsel A test-now vs B defer/narrow); then `/red-team` (2 HIGH breaks folded, below). PM decided.
- Context: issue #145 asks whether to extend the vendored trigger-testing instrument (ADR 0033) to `advise`/`red-team`/`verify` — the three model-invocable, always-loaded pdca descriptions. ADR 0016 shipped them without `disable-model-invocation`, with tight "Use when" triggers and a reactive REOPEN-IF: "a primitive auto-fires on unrelated turns or burns agents unasked" (0016:28). Open question: pay the instrument proactively, or wait for that trigger to fire.

## Decision
1. **Decline the proactive instrument. Inherit ADR 0016** — its REOPEN-IF (0016:28) governs; not widened. Zero wasteful fires observed since 2026-07-07.
2. **Mechanize the reactive trigger (the break-1 repair).** The primitives emit NO git artifact (`advise` SKILL.md:3 "Advice only, no ADR"), so the retrospect git-signal arm (agents/retrospect.md:15-27) is blind to a spurious fire in an autonomous session — 0016's "free backstop" does not exist there. Ship a **PreToolUse spawn-log hook** in `pdca-workflow/hooks/` matching the Skill tool: append every `advise|red-team|verify` fire to a git-visible session log the retrospect arm reads. Rung-2 detect-at-creation on ADR 0047's ladder ("make the unobservable observable"), reusing the hooks infra ADR 0040 ships; piggybacks the hook wave. BINDING: until it ships, the backstop is interactive-only.
3. **Pre-commit the fire-path, 8+8 BOTH arms.** On the FIRST spawn-log-visible or observed misfire of any of the three, author an **8 should-fire + 8 should-not-fire** set (the toolkit-grid convention, trigger-kit/FINDINGS.md:3) for THAT skill only, via the runner (ADR 0033), appended as a dated `benchmarks/` dir (ADR 0026) — piggyback the next benchmark, not a standalone run, not all three. Should-not-fire guards the panel-spawn class; should-fire guards the false-negative/Wrong-PASS class 0016:13 exists to prevent.
4. **No description rewrites absent a measured delta** (ADR 0033 / PR #97 pattern).

## Justification
Poka-yoke + muda. The tight descriptions (0016: 777 chars) ARE the prevention; the reactive trigger is the backstop — but a backstop must be able to fire, and in autonomous mode it could not (break 1). The cheap fix is rung-2 observability (the spawn-log), NOT the probabilistic instrument: authoring 8+8 x 3 up front, with a per-run owner unblock (the kit HARD-DENIES under auto-mode — untrusted-code + self-modification — trigger-kit/FINDINGS.md:15-20), for zero observed misfires fails ADR 0024's cost-per-decision test. Mechanize the trigger now (near-zero); pay the instrument reactively when a real fire earns it.

## Assumptions
- [unverifiable] **The spawn-log hook is delivered in the hook wave — until it is, an autonomous misfire stays undetectable and the deferral's risk accrues silently.** The load-bearing weak point (break 1). Owner: PM. REOPEN-IF the hook slips the wave or cannot match the Skill surface -> the backstop is interactive-only; re-weigh paying the instrument proactively.
- [unverifiable] This repo's zero-misfire traffic is representative of consumer traffic — consumers run different query distributions with no 0016 wiring (break 3). REOPEN-IF any consumer reports a primitive misfire.
- [checkable] No `advise`/`red-team`/`verify` misfire logged since 2026-07-07 — owner: PM vs git log + `docs/decisions`; result: **verified** (only runner-tooling fixes #104/#122 and building-skills trims #97/#30; the grep hits are 0016's own REOPEN-IF text, no observed instance).
- [checkable-doc] Deferring contradicts no accepted ADR — the full paired benchmark is out of scope (no valid "without" arm, #145 body) and ADR 0024 argues against proactive spend; result: verified.

## Rejected alternatives
- Test now, full TP/FP x 3 (counsel A) — feasibility (runner runs) is not warrant; spends on a zero-frequency risk.
- Pure defer, "nothing to build" (the draft red-team broke) — the reactive trigger is blind in autonomous mode without an artifact; hence the spawn-log hook, not a bare wait.
- Reactive set should-not-fire ONLY (counsel B fallback) — forecloses the false-negative/Wrong-PASS detector 0016:13 targets; the should-fire arm is near-free once the fixed cost is paid.
- Widen 0016's REOPEN-IF to fire proactively — re-litigates a settled ADR with no new signal.
- Rewrite the three descriptions tighter now — no measured delta; risks regressing skills that fire correctly (funding-cuts precedent).

## Revisit triggers
- A primitive fires unbidden (spawn-log-visible or observed) -> run the 8+8 set for that skill; trim per ADR 0033 / PR #97 if the description is at fault.
- A verification-worthy small call ships with NO primitive fired (false-negative) -> re-weigh trigger breadth (break 2b).
- The spawn-log hook slips the wave or can't match the Skill tool -> backstop stays interactive-only; re-decide proactive spend.
- The three descriptions grow or multiply (0016's own re-audit trigger) -> re-weigh always-loaded cost.
- Claude Code ships per-skill fire-rate telemetry -> replace this judgment call with measured rates; the kit becomes unnecessary.
