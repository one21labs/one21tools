# Reference audit: 2026-07-18 loop-engineering sweep (adversarial fetch-audit)

First run of the reference-veracity rule (owner ruling: gates, period; lane "verified" labels
are reports, not verification). Method: an adversarial agent instructed to DISPROVE every
external reference in the corpus, the three lane files, the README positioning section, and
issues #236/#240 — direct fetch of each URL/arXiv abstract/repo (GitHub API for star counts),
quote located in the fetched source or the item fails.

## Result: 24 VERIFIED / 2 MISATTRIBUTED / 1 STRUCK / 3 UNREACHABLE-corroborated / 0 fabricated IDs

**Defects found and corrected (same-day):**
1. **arXiv:2606.19826 MISATTRIBUTED** — cited (corpus, sota-lane, issue #236 item 12) as the
   anchor for "multi-agent debate does not reliably beat single-agent baselines"; the paper is
   actually "Heterogeneous LLM Debate Under Adversarial Peers" — adversarial-peer robustness,
   a different question. Fixed: claim relabeled UNSOURCED everywhere; the correct citation is
   an open item.
2. **Harvey "~6x" STRUCK** — the Dreams docs page (fetched in full) contains no Harvey or 6x
   figure; the claim traces only to near-identical content-farm blogs. Annotated as struck in
   `2026-07-18-claude-sota-lane.md` (raw lane text preserved as the record of what the lane
   reported).
3. **GEPA/ACE conflation** (sota-lane) — "Generator/Reflector/Curator" is ACE's mechanism, not
   GEPA's; GEPA's measured gain is +6% avg (up to 20%) over GRPO, >10% over MIPROv2 — not
   "+8-10%". Annotated in the lane file.
4. **Karpathy X post over-labeled** — sat in the corpus "verified primaries" table despite a
   login-wall (HTTP 402); nobody here has fetched it. Relabeled CORROBORATED ONLY.

**Held up under direct fetch (selection):** the Boris Cherny quote (technologyreview.com
2026/05/21/1137735 — verbatim match; the highest-risk item); every other arXiv ID in scope
(2606.11217, 2606.27687, 2605.27276, 2607.14890, 2605.28282, 2602.12670 core stats,
2510.04618, 2403.16971); all four GitHub star counts (exact); the Dreams + memory docs pages;
Weng's post; Mukta's talk (oEmbed title match); andrewyng/context-hub (README quote verbatim);
the LangChain/StackHawk/Osmani posts; skillsbench.ai; agentskills.io.

**Unreachable (corroborated by independent secondaries, NOT verified):** Karpathy X post
(login-wall); openai.com/index/harness-engineering (403 bot-block; InfoQ/Latent Space
corroborate author/date/content); YC library page body (JS-rendered, title confirmed).

**Residual notes:** SkillsBench "Phase 3 self-generated skills flat/negative" not found in the
fetched abstract excerpt (likely appendix) — not contradicted, downgrade to plausible;
obra/superpowers stars measured live at 256,771 (docs deliberately cite no number).
