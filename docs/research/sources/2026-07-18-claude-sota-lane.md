# Lane output: Claude web agent — SOTA systems survey (2026-07-18)

Raw report summary, committed for audit (distilled corpus: ../loop-engineering.md). Methodology:
5 parallel sub-lanes; load-bearing claims re-verified against primary sources; unverified items
excluded from the ranked list.

## Ranked shortlist (what they do we don't / what we do they don't)
1. Anthropic Dreams (Managed Agents preview, May 2026) — async transcript+memory merge into a NEW reviewable store, never mutates source; Harvey reports ~6x task-completion gains. No decisions/panel/gates.
2. Anthropic skill-creator (anthropics/skills) — paired with/without subagent runs (aggregate_benchmark.py) AND description optimization with 60/40 train/test split, 3x repeats, 5 rounds. Graders/comparators instructed NEUTRAL ("Don't favor outputs based on style preferences"); no prosecutor, no cross-family judge, no pre-registration/cost gates.
3. Letta (ex-MemGPT, 23.8k stars) — OS-style paged memory (core/recall/archival). No governance layer.
4. AIOS (6.1k stars, COLM 2025, arXiv:2403.16971) — literal agent OS: scheduler + context/memory managers, 2.1x throughput. No decision/red-team concept.
5. Kulaxyz/self-learning-skills (887 stars, active) — autonomous SKILL.md writing, NO approval gate; 3-condition promotion (passing check + named failure pattern + ruled-out dead end).
6. GEPA (arXiv:2507.19457, ICLR 2026 oral) / ACE (arXiv:2510.04618) — reflective evolution, Pareto candidate frontiers, Generator/Reflector/Curator; +8-10% quantified. No auditable decision record.
7. bitwarden/ai-plugins claude-retrospective (127 stars) — git+session mining -> structured reports -> proposed CLAUDE.md/SKILL.md/agent edits, human-gated. Closest /retrospect analog.
8. Augment Code "Intent" — shipped pre-merge Verifier + spec Critique agents. No red-team/ADR/retrospective.
9. robertoecf/adversarial-review + wan-huiyan/agent-review-panel — cross-family review ("the partner reviews, never the host"); 4-6 reviewer debate + supreme judge. Single-shot, no persistence.
10. Multi-agent debate lineage (Du et al. MAD, ChatEval, AI Safety via Debate) — foundational; 2025-26 literature candid that MAD does not consistently beat single-agent baselines (arXiv 2606.19826).

## Verdict
No project closes the full pdca-workflow loop as one system; the combination + the retrospect-edits-its-own-agent-definitions step look genuinely novel among findable work. skill-bench: paired with/without and trigger ablation NOT novel (skill-creator); surviving: prosecutor grading, pre-registration + cost-gating combined (verified absent from promptfoo, Inspect AI, Braintrust, LangSmith, OpenAI Evals), enforced (vs advisory) cross-family judging. Bias literature anchors: Zheng et al. NeurIPS 2023; Panickssery et al. NeurIPS 2024. Pre-registration academic anchors: arXiv:2606.11217, arXiv:2606.27687. Inspect AI's immutable EvalLog = complement pattern for post-run integrity.

## Excluded as unverified
Some single-lane arXiv IDs not re-fetched; OpenClaw star counts; Microsoft "Agent OS" branding attribution; "Qualixar OS" (low credibility).
