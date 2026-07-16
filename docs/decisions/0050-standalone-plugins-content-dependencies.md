---
id: 0050
title: "Plugin distribution: standalone plugins; dependencies only where content requires"
status: accepted
summary: "Every marketplace plugin installs standalone — no plugin declares a dependency to distribute behavior. pdca-workflow's enforcement hooks are dev tooling for repos that adopt the PDCA practice, not a product that travels with skills; where hooks should fire (per-project vs session-wide) is needs-design. A dependency arrow may exist only where one plugin's content cannot function without another's files — today that set is empty (skill-bench carries its own method references, ADR 0063 Call 2). The shared ./skills source stays; no per-plugin source split. Owner decision, recorded directly; reworked in place — git history carries the superseded original."
---

# 0050 — standalone plugins; content-true dependencies only

- Date: 2026-07-16 (reworked in place by owner decision; the original enforcement-distribution
  design and its reversal live in git history and PR #208)
- Owner: the repo owner, directly — asked, not inferred. Panel: none; the client was present.
- Context: only pdca-workflow ships hooks; the question was whether installing any skills plugin
  should pull those hooks in. The measured content-dependency graph answers it: the skills never
  need pdca-workflow (two incidental mentions corpus-wide), pdca-workflow's retrospect method
  leans on engineering-principles by name (agents/retrospect.md:33), and skill-bench owns its
  measurement method (ADR 0063 Call 2). The consumer of a lone skills plugin wants that plugin,
  nothing else.

## Decision
1. **Skills plugins install standalone** — "just that plugin, nothing else" (owner). No
   `dependencies` field anywhere; never declare a dependency to DISTRIBUTE behavior.
2. **A dependency arrow may exist only where CONTENT requires it** — one plugin's skill cannot
   function without another's files. Today that set is empty.
3. **The hooks are dev tooling** for repos that adopt the PDCA practice, not a product to push
   with skills. They stay inside pdca-workflow; WHERE they should fire (per-project opt-in vs
   session-wide) is needs-design — see revisit triggers.
4. **The shared `./skills` source stays** — no per-plugin source split; its only justification
   was carrying dependency declarations, and that justification is gone.

## Justification
Judgment, not mechanism: judge the artifact as the person on the receiving end — a stranger
installing one reference skill must not receive an opinionated process framework and
session-wide behavioral guards they did not ask for (CLAUDE-base: simplicity and user
experience above all). The content graph points away from enforcement: nothing in the skills
needs the workflow, so a forced pull served the system's values, not any user.

## Assumptions
- [verified] the skills have no functional dependency on pdca-workflow — corpus grep: two
  incidental mentions (section-ablation.md:21, token-format-efficiency.md:22), zero links.
- [checkable] each plugin installs standalone from the marketplace and its skills load — owner:
  the Testing section of any PR touching the Sacred manifests. result: the shared-source layout
  is the one in production use since extraction; re-prove on any manifest change.
- [unverifiable] no consumer is stranded by the absence of auto-pulled guardrails — REOPEN-IF a
  real adopter reports expecting the hooks to arrive with a skills install.

## Rejected alternatives
- **Enforced pdca-workflow dependency on every plugin** (this ADR's original decision) — rested
  on an owner-attributed directive with no citable source, disavowed by the owner when asked
  directly. The mechanism (fail-closed auto-install, verified live) worked; the premise was
  false. A want you cannot quote is your own want.
- **One monolith plugin** — forces every skill's description into every consumer's context and
  removes leaf choice.
- **A minimal hooks-only carrier plugin** — packages the hooks for distribution before their
  firing scope is even designed; mechanism-first, the original mistake's shape.
- **Per-plugin source split without the dependency rationale** — structure churn with no
  consumer benefit (built once, measured against this bar, discarded unmerged).

## Revisit triggers
- The hooks-scope design lands (per-project opt-in vs session-wide) -> revisit hook packaging.
- A real content dependency appears -> declare exactly that arrow, content-true, nothing more.
- Standalone installs measurably strand users (a support signal, not speculation) -> consider a
  VISIBLE recommended-companion note in the plugin description; never a forced pull.
