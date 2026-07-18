# Loop-engineering research corpus

The versioned knowledge home for research on self-improving AI loops / "AI operating systems" /
harness engineering — the field this repo's pdca-workflow and skill-bench live in. Work-state
(which improvement directions are being executed) tracks in issue #236 per ADR 0021; THIS file
owns the knowledge: verified sources, the SOTA map, tracking keywords, and the refresh method.
Raw per-lane sweep outputs are committed under `sources/` (auditable, ADR 0023 ethos).

## How to refresh this corpus (the method that produced it)

Three parallel lanes, cross-checked against each other — disagreement between lanes is itself
signal:
1. A Claude web agent on PRIMARY SOURCES: fetch-verify every load-bearing quote/claim; maintain
   the unverified-meme ledger below (this lane caught two viral misquotes).
2. A Claude web agent on SOTA SYSTEMS: name specific repos/products, verify-or-refute OUR
   differentiation claims against them (this lane deflated two skill-bench novelty claims).
3. A grok lane (`~/.grok/bin/grok --prompt-file <brief>`) for cross-family diversity + live X
   search, where this discourse appears first.

Ranking criterion for improvement directions (owner, 18-Jul-2026): would this have caught a
real recorded miss without the owner in the loop? Refresh cadence: on demand, when planning a
measurement campaign, or when a keyword below stops surfacing new signal. Update this file by
appending a new dated snapshot section; never rewrite a prior snapshot (they are the record of
what the field looked like when decisions were made).

---

## Snapshot 2026-07 (first survey; lanes: `sources/2026-07-18-*.md`)

### The thesis and its verified primary sources

The durable asset is the loop around the model (context, memory, decision records, evals,
verification gates, feedback), not the model. Verified primaries:

| Source | Claim | Ref |
|---|---|---|
| Anthropic engineering (Sep 2025) | context is a finite engineered resource | anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| Anthropic engineering (Nov 2025, Mar 2026) | initializer->coder, then planner->generator->evaluator harness cycling until the app works | anthropic.com/engineering/harness-design-long-running-apps |
| Boris Cherny, MIT Tech Review (May 2026) | the verified "have Claude prompt itself" default — verbatim quote homed in pdca-workflow/README.md ("The loop is the asset"); replaces the viral meme form | MIT Technology Review |
| Lamis Mukta, AI Native DevCon (Jun 2026) | "dreaming": scheduled offline pass reviewing sessions + curating memory stores | youtube.com/watch?v=tTcxVv8HHNw |
| Anthropic Managed Agents "Dreams" docs | offline curation over past sessions with an immutable input store (mechanics: sources/2026-07-18-claude-sota-lane.md) | platform.claude.com/docs/en/managed-agents/dreams |
| Tom Blomfield, YC (May 2026) | self-improving company: sensor / policy / tool / quality gate / learning mechanism | ycombinator.com/library/Qf-how-to-build-a-self-improving-company-with-ai |
| Karpathy (2023) | LLM-OS: model=kernel, context=RAM, tools=peripherals | x.com/karpathy/status/1723140519554105733 |
| Lilian Weng (Jul 2026) | self-improvement should target the harness layer, bounded by permissions/observability | lilianweng.github.io/posts/2026-07-04-harness/ |
| Addy Osmani (Jun 2026) | "Loop Engineering" synthesis; "the agent forgets, the repo doesn't" | addyosmani.com/blog/loop-engineering/ |
| LangChain, S. Runkle (Jun 2026) | four nested loops: agent -> verification -> production -> harness hill-climbing | langchain.com/blog/the-art-of-loop-engineering |
| OpenAI, R. Lopopolo (Feb 2026) | harness engineering: repo-as-OS, exec plans, mechanical lints, agent-agent review | openai.com/index/harness-engineering |
| Proof-or-Stop (Jul 2026) | evidence-gated lifecycle transitions | arXiv:2607.14890 |

### Unverified-meme ledger (do NOT cite as fact)

- "You're not supposed to prompt Claude. You're supposed to build a system that prompts
  itself" — no primary transcript; use the Cherny MIT-TR quote.
- "Burn tokens, not headcount" as a Blomfield quote — paraphrase only.
- "~22-point SWE-bench swing from harness vs ~1 from model" — no traceable primary benchmark.
- Mitchell Hashimoto as coiner of "Agent = Model + Harness" — likely fabricated attribution.
- "Code with Claude" event date — inconsistent across sources (May 6 vs May 19, 2026).

### SOTA map (who does what; overlap with this repo)

- **Anthropic Dreams** — productionized retrospect-adjacent memory curation; no decisions/gates.
- **Anthropic skill-creator** (anthropics/skills) — paired with/without runs + description
  optimizer with 60/40 train/test split; graders instructed NEUTRAL; no pre-registration.
- **SkillsBench** (arXiv:2602.12670, skillsbench.ai) — paired no-skills/curated-skills across
  Claude Code/Codex/Gemini/OpenHands; skill-invocation-rate leaderboard; self-generated skills
  often flat/negative (Phase 3).
- **Letta** (ex-MemGPT) — OS-style paged agent memory. **AIOS** (COLM 2025) — literal agent OS
  scheduler/context/memory managers. Infra layer, no process governance.
- **GEPA** (ICLR 2026 oral) / **ACE** (arXiv:2510.04618) — reflective prompt/playbook
  evolution, Pareto frontiers; no auditable decision record.
- **Kulaxyz/self-learning-skills** — autonomous SKILL.md writing, no approval gate,
  3-condition promotion rule. Most autonomous public loop found.
- **bitwarden/ai-plugins claude-retrospective** — closest public /retrospect analog
  (git+session mining -> proposed CLAUDE.md/skill edits, human-gated).
- **Augment Code Intent** — shipped pre-merge Verifier + spec Critique.
- **robertoecf/adversarial-review**, **wan-huiyan/agent-review-panel** — cross-family
  adversarial review mechanics in the Claude Code plugin space, single-shot.
- **obra/superpowers** + **superpowers-evals ("Quorum")** — dominant methodology plugin +
  multi-CLI eval lab grading triggering/verification reflexes.
- **Context Hub** (ambiguous name): andrewyng/context-hub (`chub`, versioned curated docs +
  feedback loop) vs LangSmith Context Hub (org registry for AGENTS.md/skills).
- Debate lineage: Du et al. MAD, ChatEval, AI Safety via Debate — with 2025-26 skepticism
  (arXiv:2606.19826): debate does NOT reliably beat single-agent baselines.

**Field verdict:** no found project closes pdca-workflow's full loop (panel -> ADR ->
verify/red-team -> self-editing retrospective) as one system; every piece exists in isolation.

### This repo's differentiation, with empirical status (owner standard: different != better)

- NOT novel: paired with/without skill evals; trigger ablation (skill-creator, SkillsBench).
- Surviving + measured: **prosecutor grading** (raised the battery delta +0.075 -> +0.088 by
  shaving inflated baseline credit, `benchmarks/2026-07-08-skills-hermetic`); **cross-family
  judging** (two caught verdict flips — #172 prototype, bs-iter2 in
  `benchmarks/2026-07-17-crossjudge-regrade` — nine robust holds).
- Surviving + observed-saves-only (no controlled comparison): **pre-registration + cost
  gates** (the 3.5x estimate-miss catch, ADR 0066/0076 trail); academic anchors for the
  vocabulary: arXiv:2606.11217, arXiv:2606.27687.
- Unmeasured against alternatives: **the integrated loop itself** — honest nulls recorded in
  the pdca-workflow README "Measured" section; panel-vs-single-advisor comparison queued (#236).

### Tracking keywords (the terms that surface signal)

loop engineering; harness engineering; context engineering; context rot / context pollution;
agent skills / SKILL.md / agentskills.io; SkillsBench / paired skills evaluation; skill
invocation rate / description ablation; Claude Managed Agents Dreams / memory curation /
dreaming; LLM OS / Letta / MemGPT / AIOS; agentic context engineering (ACE); GEPA reflective
prompt evolution; DSPy MIPROv2 / SIMBA; TextGrad; self-evolving agents survey; LLM judge
self-preference bias / cross-family LLM judge; multi-agent debate baseline (skepticism:
arXiv:2606.19826); pre-registration LLM evaluation; evidence-gated / Proof-or-Stop; Ralph
Wiggum loop; doc-gardening agent; agent legibility; maker-checker / plan build judge; claude
code retrospective plugin; self-learning-skills; memory tool 20250818; superpowers-evals
Quorum; context hub / chub; comprehension debt / intent debt. Caution: "OS Agents survey" =
GUI/computer-use agents (different sense).

### Improvement directions

Ranked list (Dreaming layer; evidence-gated lifecycle transitions; bounded autonomous
promotion; panel-vs-single measurement; decay lifecycle; Pareto-frontier ADRs; and the five
skill-bench items incl. train/test-split description tuning and the immutable post-run log)
lives as the actionable checklist in **#236** — one home for work-state (ADR 0021). When one
is executed, its outcome links back from that issue; when all are resolved, the next snapshot
here records what the field looked like at that point.
