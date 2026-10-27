# Decision log — one21tools

Authoritative Decision Records (ADRs) for this repo's meta/tooling judgment calls (plugin scope,
marketplace shape, process).

**The rules, the template, the no-index-file rationale, and the size budgets live in the plugin:**
[pdca-workflow/skills/decide/references/adr-template.md](../../pdca-workflow/skills/decide/references/adr-template.md).

Guard: adr-lint — command in [CLAUDE.md](../../CLAUDE.md), spec in
[adr-lint.md](../../pdca-workflow/skills/decide/references/adr-lint.md).

## Retired ids

Records retired under the ADR altitude test (home: doc-budgets.md); a cite of one resolves HERE:

- 0001 -> pdca-workflow/skills/decide/references/metrics-engine.md (spec-not-runnable rationale, top)
- 0002 -> docs/decisions/README.md (ADR = Authoritative Decision Record)
- 0003 -> pdca-workflow/skills/decide/references/adr-lint.md (UNFALSIFIABLE presence gate)
- 0004 -> pdca-workflow/skills/pdca-init/references/panel-generation.md (step 4, version-control the panel)
- 0005 -> pdca-workflow/skills/retrospect/SKILL.md (step 7, /simplify; run-coupled built-ins deliberately unnamed in verifier.md)
- 0006 -> pdca-workflow/agents/retrospect.md (model: sonnet; frontmatter is the tier SSoT)
- 0009 -> skills/building-skills/scripts/validate.py (design comment above BODY_MAX_CHARS)
- 0010 -> skills/building-skills/scripts/validate.py (design comment above BODY_MAX_CHARS)
- 0011 -> pdca-workflow/skills/pdca-init/SKILL.md (COPY default); pdca-workflow/scripts/adr-lint.mjs (manifestDrift)
- 0012 -> .github/workflows/gates.yml (header: required-CI rationale)
- 0013 -> one21labs/skill-measure:skills/bench/references/empirical-evals.md (delegated harness); one21labs/skill-measure:scripts/eval_verdict.py
- 0014 -> pdca-workflow/skills/retrospect/SKILL.md (step 4, self-check + no-extractor rule)
- 0015 -> CLAUDE.md (Stack & navigation commands; test-command mirror deleted, gates.yml owns it)
- 0016 -> pdca-workflow/README.md (invocation paragraph: panel primitives model-invocable); bench condition: one21labs/skill-measure:scripts/lib/spend_guard.py header
- 0017 -> CLAUDE.md (no plugin version fields; sole drift predicate adr-lint.mjs manifestDrift)
- 0018 -> pdca-workflow/agents/retrospect.md (Method, backstory-sweep clause; reopen: recurrence -> a dedicated pre-PR doc-review step, not a bigger prompt)
- 0020 -> pdca-workflow/skills/decide/references/adr-template.md (## Lite tier)
- 0021 -> CLAUDE.md (Shipping - PR, Findings valve)
- 0022 -> .claude/settings.json (extraKnownMarketplaces: directory source ./)
- 0025 -> one21labs/skill-measure:skills/bench/references/cost-and-verdict.md (## Scoring: fraction-met, prosecutor min rule)
- 0026 -> one21labs/skill-measure:scripts/lib/README.md (bench_io record formats + raw-output archive)
- 0027 -> one21labs/skill-measure:scripts/lib/verdict.py (merge_verdict: directional merge bar)
- 0028 -> docs/decisions/panel.md (tracked repo panel; adr-lint.mjs agent-home checks)
- 0029 -> scripts/check-workflow.mjs (header)
- 0031 -> one21labs/skill-measure:skills/bench/references/section-ablation.md (relocated Tier 2; 0/0 rule in empirical-evals.md)
- 0032 -> pdca-workflow/skills/decide/references/adr-template.md (tag-routing, named-signal pending rule)
- 0033 -> one21labs/skill-measure:skills/bench/references/description-ablation.md (instrument + validity); one21labs/skill-measure:scripts/run_eval.py (header)
- 0034 -> one21labs/skill-measure:skills/bench/references/empirical-evals.md (0/0 cell = measurement failure); benchmarks/2026-07-09-claude-md-sections/
- 0035 -> benchmarks/2026-07-10-tiered-execution-fullgrid/README.md (Correction: verdict, adopt_tiered false)
- 0036 -> benchmarks/2026-07-10-routing-escalation/README.md (Result: DO NOT ADOPT)
- 0037 -> benchmarks/README.md (cited evidence lands on main)
- 0038 -> skills/engineering-principles/references/jit-documentation.md (Decision Test, shipping-boundary row)
- 0039 -> skills/engineering-principles/references/waste-identification.md + ssot-enforcement.md + jit-documentation.md; skills/building-skills/references/validation-rules.md
- 0040 -> pdca-workflow/hooks/explicit-model-guard.sh (header); skills/building-skills/scripts/validate.py (R8)
- 0042 -> one21labs/skill-measure:skills/bench/references/pre-registration.md (cite methodology; cost-pilot; prior-art pass)
- 0043 -> CLAUDE.md (Shipping - PR, Sync before spend)
- 0044 -> skills/building-skills/scripts/validate.py (R6.2)
- 0045 -> git history (upstream filing declined; issue #94 closed not-planned)
- 0046 -> scripts/check-restatement.mjs (header); pdca-workflow/templates/claude-review.yml (one-home line)
- 0048 -> CLAUDE.md (no plugin version fields; bump cadence is a dead path)
- 0049 -> pdca-workflow/hooks/spawn-log.sh (header); pdca-workflow/agents/retrospect.md (Telemetry logs)
- 0050 -> README.md (Requirements: each plugin installs standalone)
- 0051 -> pdca-workflow/skills/decide/references/adr-template.md (PR is the decision-batching unit); adr-lint.md (check 12)
- 0052 -> one21labs/skill-measure:scripts/lib/cost_gate.py (header); one21labs/skill-measure:scripts/lib/blind.py (header)
- 0053 -> .github/workflows/gates.yml (header: branch-protection settings)
- 0054 -> scripts/check-pr-body.mjs (header, title/Partial guard)
- 0055 -> one21labs/skill-measure:scripts/lib/substrate.py (header); one21labs/skill-measure:skills/bench/SKILL.md (judge default, subcommands)
- 0058 -> one21labs/skill-measure:skills/bench/SKILL.md (--reps default); one21labs/skill-measure:scripts/lib/substrate.py (PIN comment)
- 0059 -> one21labs/skill-measure:skills/bench/references/pre-registration.md (No primed conclusions)
- 0060 -> .claude/hooks/budget-edit-guard.sh (header)
- 0061 -> benchmarks/2026-07-13-pdca-decide-armd/ + benchmarks/2026-07-12-pdca-decide-outcome/README.md (outcome); next steps ADR 0062
- 0063 -> one21labs/skill-measure:README.md (method references ship in-plugin; #170 set shipped)
- 0064 -> .github/workflows/gates.yml (comment above the test-*.sh loop, hook-test convention)
- 0065 -> one21labs/skill-measure:skills/bench/references/pre-registration.md (Saturation/floor pre-screen + Design-for-signal; reopen clause ends the pre-screen section)
- 0066 -> one21labs/skill-measure:skills/bench/references/cost-and-verdict.md (grading-cost estimate line)
- 0067 -> pdca-workflow/scripts/adr-lint.mjs (marginWarnings header); adr-lint.md (check 7)
- 0068 -> benchmarks/2026-07-15-pdca-retrospect-friction-phase0/README.md (verdict; #189 closed)
- 0069 -> git history (check-gate-tests.mjs deleted, #311)
- 0070 -> benchmarks/README.md (same-PR reconcile rule; hoisted by PR #216)
- 0072 -> .claude/hooks/three-dot-warn.sh (header, diff-only predicate)
- 0073 -> one21labs/skill-measure:skills/bench/references/cost-and-verdict.md (ceiling_usd = 2x estimate)
- 0074 -> .claude/output-styles/plain-summary.md (+ pdca-workflow/templates/plain-summary.md)
- 0075 -> CLAUDE.md (Shipping: plugins carry no version fields; absence is the enforcement)
- 0076 -> one21labs/skill-measure:skills/bench/references/cost-and-verdict.md (derived estimates + warn escalation)
- 0077 -> git history (merge=union attribute dropped when the logs went local, ADR 0080 (c))
- 0078 -> scripts/check-pr-body.mjs (body-side closing-keyword guard)
- 0083 -> pdca-workflow/agents/retrospect.md (Method, Custodial state)
- 0085 -> README.md (Provenance) + each shipped plugin README's Provenance section
- 0087 -> pdca-workflow/scripts/adr-lint.mjs (lite Enforced: check); adr-lint.md (check 6)
- 0088 -> pdca-workflow/scripts/adr-lint.mjs (docIndexDrift + stale-discharge comments)
- 0091 -> pdca-workflow/skills/retrospect/SKILL.md (step 5, unearned provenance + delete test)
- 0094 -> pdca-workflow/agents/retrospect.md (Custodial state, backlog); pdca-workflow/scripts/issue-hygiene.mjs (header)
- 0098 -> one21labs/skill-measure:skills/bench/references/judging.md (prosecutor scoped to verdict path); backlog: issue one21labs/skill-measure#1 — if it closes with the stats menu unaddressed, re-file survivors singly
- 0099 -> one21labs/skill-measure:scripts/lib/usage_guard.py (header); one21labs/skill-measure:skills/bench/references/cost-and-verdict.md (usage-limit pause)
- 0100 -> benchmarks/2026-10-12-g8-shortfall/metadata.json (stop rule) + README.md (Measured state)
