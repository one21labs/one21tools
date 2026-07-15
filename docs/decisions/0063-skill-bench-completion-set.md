---
id: 0063
title: "skill-bench completion set: ratify 0055, keep method-reference home, bundle #191 1-3, defer paid runs"
status: accepted
summary: "Four calls completing #170: (1) flip ADR 0055 proposed->accepted, amended; (2) method references KEEP in building-skills (skill-bench references them) — mitigate lone-install loss by naming the dev-skills plugin, not moving; (3) bundle #191 items 1-3 + item-4 checklist half, split the cross-plugin verifier edit + item 5; (4) defer paid M5/M6 to issues, #150 keeps its own PR, but the zero-spend /plugin install round-trip rides this PR. Also completes M3, ships templates, refreshes README, cuts the lib husk."
---

# 0063 — skill-bench completion set (#170)

- Date: 2026-07-14
- Owner: PM
- Panel: plugin-adopter, lean-process-engineer, process-economist (session-operator dropped — no live-session question). Opposing counsel ran on Call 2; Calls 1 + 4 UNANIMOUS accept — a scope signal.
- Context: #170 extracts the repo's only public hermetic skill-measurement pipeline. ADR 0055 sat `proposed` while M1/M2/M4 shipped gate-green (skill-bench/, marketplace:39, lib move, config layer, grok judge default judge.py:57, pinned promptfoo substrate.py:78 / ADR 0058). Gaps blocking #170 acceptance: M3 partial (`/bench` has skill+verdict, no `trigger`; run_eval.py/eval_verdict.py still at skills/building-skills/scripts/), templates absent (owner #170 comment), README.md:1 stale ("nothing on the marketplace" — false), benchmarks/lib a .gitignore husk, /plugin install unproven (README:93). Owner directive 2026-07-14: package related work into the next PR.

## Decision
**Call 1 — flip ADR 0055 proposed->accepted, amended** (applied to 0055 this PR): items 2-3 shipped as decided (judge.py:57, substrate.py:78), item 4 partial (no `trigger`); item 1's reference clause shipped INVERTED — refs stay in building-skills, skill-bench references them (SKILL.md:64, judging.md:11), opposite of 0055:16. Weakest assumption now discharged (below). Status = decision validity, not milestone completion — the flip does not wait on M3.
**Call 2 — method references KEEP in building-skills** (ratify the inversion). SSoT is met by the cross-reference; a move rewrites cross-links + external pointers and re-certs dev-skills for no poka-yoke. Mitigate the lone-install adopter loss: skill-bench/README requirements + judging.md:11 must name the **dev-skills plugin**, not just "the building-skills skill".
**Call 3 — bundle #191 items 1-3 + item-4's bench-SKILL.md checklist half into THIS PR**, each its own commit (skill-bench-local, additive to resident files). Split item-4's pdca-workflow verifier-agent edit (cross-plugin revert boundary) + item 5 to a follow-up issue.
**Call 4 — defer paid M5/M6 to follow-up issues; #150/ADR 0050 keeps its own PR.** Carve-out: the zero-spend `/plugin install` round-trip (README:93) rides THIS PR, proven in Testing — first command an adopter types.
**Also this PR** (owner directive): complete M3 (move run_eval.py/eval_verdict.py into skill-bench/scripts/ + `/bench trigger`, documenting hard-problems 3 Workflow-dependency + 4 Linux/WSL), ship the canonical grid-runner/blinding/grading-workflow templates, refresh the README, cut the benchmarks/lib husk. Deferred = issues (ADR 0021).

## Justification
Owner directive + ADR 0056 (cohesive over one-concern) drive one packaged PR; split lines are revert boundaries, not concern counts. Keep (Call 2) is same-SSoT at zero churn — #170's "no reference duplicated" bar is already met (zero evals cases exercise the five filenames), so a move is a paid ADR-0024 re-check for cosmetic compliance. #191 1-3 are additive to resident files, cohesive with the extraction; the verifier-agent edit is cross-plugin (clean revert), so it splits. #150 is a Sacred restructure with no code dependency here (ADR 0050).

## Assumptions
- [verified] 0055's WEAKEST assumption — a grok re-grade of a dated benchmark reproduces the divergence diagnostic — is DISCHARGED: poker `bench_verdict.py --judge both` gives agreement 0.819, kappa 0.593 (`benchmarks/2026-07-14-pdca-decide-poker/README.md:66,101`), a second point beside the 72-cell prototype (kappa 0.575).
- [checkable] #191 items 1-3 change no shipped call signature (helper added to bench lib; blind.py/benchstats.py extended additively) — gate verifies at build.
- [checkable] M3 move is behavior-neutral: run_eval.py/eval_verdict.py + tests relocate to skill-bench/scripts/, gates stay green — gate verifies.
- [checkable-doc] no plugin.json carries a `dependencies` field (grep: none), so the dev-skills dependency is README prose here, NOT declared; #150/ADR 0050 (which introduces that field) stays a separate PR, no code dependency. result: verified.
- [unverifiable] naming the dev-skills plugin in README + judging.md closes the lone-install adopter loss. REOPEN-IF a real external adopter installs skill-bench alone and still hits a dangling method pointer.

## Rejected alternatives
- MOVE the five references into skill-bench (Call 2 losing counsel) — rewrites 9+ cross-links + 3 external pointers, re-certs dev-skills, machine-unverified either way; #170's duplication bar already met. Churn, no poka-yoke.
- Fast-follow ALL of #191 (adopter) / split ALL of #191 (lean) — owner directive packages related work; the middle splits only the cross-plugin edit on its revert boundary.
- Bundle #150 here — Sacred restructure, different revert boundary, no code dependency (ADR 0050).
- Leave 0055 `proposed` — drift-by-omission while reality diverged on two of four items.
- Ride /plugin install on the M5/M6 deferral — it is zero-spend and the #170 acceptance bar.

## Revisit triggers
- First external adopter installs skill-bench alone, or M6 external proof runs — reopens Call 2.
- A #191 1-3 change forces a shipped call-signature edit — revert boundary broke; reopens Call 3.
- /plugin install fails in Testing — 0055 M6 blocked; #170 acceptance not met.
