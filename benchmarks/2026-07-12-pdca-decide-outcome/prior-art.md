# Prior-art survey — LLM decision-quality + LLM-judge methodology (for #172 pre-registration)

## 1. Structured deliberation vs compute-matched baselines
- Smit et al., "Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs" (ICML 2024, arXiv:2311.17371) — MAD does not reliably outperform self-consistency/ensembling at comparable inference cost; hyperparameter-fragile.
- Zhang et al., "If Multi-Agent Debate is the Answer, What is the Question?" (2025, arXiv:2502.08788) — 5 MAD methods x 9 benchmarks x 4 models: MAD fails to beat CoT/self-consistency even while consuming more compute. Model heterogeneity is the one consistent fix.
- "Reasoning in Token Economies: Budget-Aware Evaluation of LLM Reasoning Strategies" (EMNLP 2024, arXiv:2406.06461) — token-budget-matched comparison: much of the apparent gain of elaborate scaffolds disappears.
- Chen et al., "Are More LLM Calls All You Need?" (NeurIPS 2024, arXiv:2403.02419) — performance non-monotone in call count.
- Huang et al., "LLMs Cannot Self-Correct Reasoning Yet" (ICLR 2024, arXiv:2310.01798).
- Outcome-scored decision benchmarks (not deliberation-structure): EconEvals (arXiv:2503.18825), DSGBench (arXiv:2503.06047).
- **Gap: all compute-matched results are on verifiable tasks (math/QA/games). Whether structure beats token-matched unstructured deliberation on OPEN-ENDED judgment is unpublished — the open regime.**

## 2. Backtesting against known outcomes / contamination control
- Karger et al., "ForecastBench" (ICLR 2025, arXiv:2409.19839) — only questions unresolved at submission; continuously regenerated.
- Halawi et al., "Approaching Human-Level Forecasting with Language Models" (NeurIPS 2024, arXiv:2402.18563) — restrict test set to questions opened after model cutoff + timestamp-restricted retrieval; the standard hindsight-leakage recipe. Predecessor: AutoCast (Zou et al., NeurIPS 2022).
- 2026: naive backtests inflate via temporal leakage ("profit mirage") — arXiv:2602.17234, arXiv:2606.22719.

## 3. LLM-as-judge validity
- Zheng et al., MT-Bench/Chatbot Arena (NeurIPS 2023, arXiv:2306.05685) — position, verbosity, self-enhancement bias.
- Wang et al., "LLMs are not Fair Evaluators" (ACL 2024, arXiv:2305.17926) — order sensitivity.
- Panickssery et al. (NeurIPS 2024, arXiv:2404.13076) + arXiv:2410.21819 — self-preference tied to self-recognition.
- Style/format normalization: Dubois et al., Length-Controlled AlpacaEval (arXiv:2404.04475); Chatbot Arena style control / Arena-Hard (arXiv:2406.11939) — regress out length/markdown before grading. These control style POST HOC statistically; rewriting outputs to a canonical schema pre-grading (blind.py's approach) has little published validation — named residual.
- Mitigation survey: arXiv:2604.23178 — position-swapping, judge panels, rubric decomposition, reference-anchored scoring.

## 4. Seeded-defect recall for review tasks
- Injected-bug code-review benchmarks: arXiv:2509.01494; survey arXiv:2602.13377; CR-Bench (arXiv:2603.11078) — precision/recall/F1 on injected defects. Industry critique (DeepSource): synthetic LLM-injected bugs may not match real-defect distribution.
- Closest to recall-on-seeded + precision-on-nonseeded: SecLLMHolmes, Ullah et al. (IEEE S&P 2024, arXiv:2312.12575) — paired vulnerable/patched code; LLMs flag clean code at near-random precision.
- **Gap: the metric pair is only loosely precedented and essentially unstudied for non-code review/audit tasks.**

## Open-regime summary (ADR 0042 prior-art rule)
Q2/Q3 settled recipes exist (adopt them). Q1 open for open-ended decision quality — exactly Instrument 2's C-vs-B question; published priors PREDICT C~B, making C>B a genuinely falsifiable, informative bar. Q4 partially precedented (code only) — Instrument 1 is novel territory for process-review tasks.
