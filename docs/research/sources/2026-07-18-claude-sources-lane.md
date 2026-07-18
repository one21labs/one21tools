# Lane output: Claude web agent — primary-source verification (2026-07-18)

Raw report, committed verbatim for audit (see ../loop-engineering.md for the distilled corpus).

Every specific claim below was independently verified by direct fetch of the primary source.

## The 8 load-bearing ideas
1. Context is a finite resource to be engineered — Anthropic Engineering, Sept 29 2025.
2. Loop engineering: leverage moved from prompt phrasing to designing the recurring system — Steinberger (X, Jun 7 2026); Osmani "Loop Engineering" (same day, "the agent forgets, the repo doesn't"); Runkle/LangChain "The Art of Loop Engineering" (Jun 16 2026): four nested loops incl. harness hill-climbing.
3. The harness — not the model — is the durable moat — Wang (Mar 2026), Jarc (May 2026, "Agent = Model + Harness. If you're not the model, you're the harness"), Masood (Jun 2026, "The model is rented. The eval is owned."); lineage: Karpathy LLM OS (Sep/Nov 2023).
4. Harness engineering as bounded self-improvement — Lilian Weng (Jul 4 2026): target orchestration, not weights; bounded by observability/permissions.
5. Anthropic reference implementation: Planner -> Generator -> Evaluator cycling — Rajasekaran (Mar 24 2026); precursor Young (Nov 26 2025, no judge role yet).
6. Agent-managed memory + dreaming — Managed Agents docs (content_sha256 optimistic concurrency, read scoping); "dreaming" as scheduled offline session/memory curation; Cherny verified quote via MIT Tech Review (May 21 2026). The viral "you're not supposed to prompt Claude..." wording is UNVERIFIED (meme).
7. Company-scale loop — Blomfield YC talk (~May 2026, ycombinator.com/library/Qf-...): five layers; overnight self-repair example verified-by-convergence (not primary-verified); "burn tokens not headcount" NOT verified as a quote.
8. "Context Hub" ambiguous — best candidate andrewyng/context-hub (chub, The Batch Mar 6 2026, "a loop where agents get better over time"); also LangSmith Context Hub (argues context > harness); plus an unrelated DataHub product.

## Convergence/divergence
All sources converge on: models commoditize, the surrounding system accumulates the value (traces to Karpathy 2023). They diverge on scope: Anthropic/Osmani = human-designed loops improving session output; Weng + "SIA" (arXiv 2605.27276) = harness modifying itself; Blomfield = same shape at org level. No agreed vocabulary; at least one prominent attribution (Hashimoto coining "Agent = Model + Harness") appears fabricated.

## Explicitly unverified
- "You're not supposed to prompt Claude..." verbatim (no transcript).
- "Burn tokens, not headcount" as Blomfield's words.
- "Code with Claude" event date (May 6 vs May 19 2026 conflict).
- The 22-point SWE-bench harness-swing stat.
- Hashimoto attribution.
- YC overnight self-repair anecdote's exact wording.
