# Panel generation — build a project-tailored advisor roster

The meta-roles (`pm`, `tech-lead`, `red-team`, `verifier`, `retrospect`) are domain-agnostic and
ship with the plugin. The **advisor panel** is not — it must be generated for each project so the
PM hears the lenses that actually matter for this product. Generate it once at `/pdca-init`;
regenerate or top it up when `/roadmap-review` finds the panel missing or stale.

## Why a custom panel
A correctness panel finds problems but can't decide between them; the PM decides, but only as
well as the lenses feeding it. The wrong panel (generic or borrowed from another domain) gives
confident, irrelevant advice. The right panel has one advisor per distinct way THIS product can
be wrong, plus the decision axes those correctness experts don't own.

## Method
1. **Infer the domain and failure modes.** From the project read (CLAUDE.md, README, manifest,
   source headers): what does the product compute or do, for whom, and how can it be
   *confidently wrong* in a way a user acts on? Each distinct failure mode is a candidate
   correctness advisor.
2. **List the decision axes.** Beyond "is it right," what decides priority/scope/gating here?
   Typically: build effort (a solo/indie engineer), willingness-to-pay (the economic buyer),
   differentiation (market/competitors), and any domain risk axis (safety, compliance, ops,
   data/privacy). Each axis the correctness experts don't own is a candidate advisor.
3. **Pick 4-8, no overlap.** One home per lens — if two candidates answer the same question,
   merge them. Fewer, sharper advisors beat a crowd; the PM picks a subset per call anyway.
4. **Write each advisor** into `.claude/agents/` from `advisor-template.md`. Give it a concrete
   real-world persona (a role a real person holds), the ONE lens it owns, and `model: sonnet`.
5. **Record the roster.** Write `docs/decisions/panel.md`: each advisor, its lens, and one line
   on why this project needs it. This is what the user edits to tune the panel.

## Two groups (label them in panel.md)
- **Correctness experts** ("is it right + useful") — one per failure mode from step 1.
- **Decision axes** the correctness experts don't own — from step 2.

## Worked example — a PID loop-tuning tool
- Correctness: `control-theory-engineer` (tuning-rule math, stability margins),
  `process-dynamics-engineer` (plant model / FOPDT fit realism), `dcs-operator` (does the
  recommendation survive a real loop, in real units, on a real controller).
- Decision axes: `buildability` (solo dev — effort/scope), `economic-buyer` (maintenance
  supervisor — willingness-to-pay/gating), `market-analyst` (vs existing tuning tools),
  `safety` (interaction with trips/SIS — ad-hoc, invoke only when a call touches it).

Adapt the names and lenses to the real project; do not ship the example roster verbatim.
