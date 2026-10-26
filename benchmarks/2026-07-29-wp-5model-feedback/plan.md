# Repo state: consistency + alignment findings and plan

**Status:** ACTIVE (2026-07). P0 SHIPPED (PR #320 merged 28-Jul). P1 DECIDED (ADR 0095, PR #321
open awaiting owner merge; gated by verifier/red-team/grok/session-operator). 0089 stub call
DECIDED + IMPLEMENTED in #321. 29-Jul /decide (PR #321): ADR 0096 claims-name-their-path
(implemented), ADR 0097 skill-assay rename (executes LAST, own PR, owner merge = consent),
ADR 0098 backlog-to-#310 + prosecutor unclaimed, ADR 0093 anti-priming amendment (persistence
implemented; --blind + separation deferred/decided). Remaining: P2 decides for #310/#317/#302
dispositions, P3 lever-1 rebalance, rename execution PR (skill-assay CONFIRMED by owner
29-Jul), first G>=8 batch, and the ADOPT track (owner-endorsed 29-Jul): /decide + own PR for
the Inspect AI substrate swap (~10pd, adapter seam exists — runtime dollar limits,
multi-provider judging, sandboxing); smaller adoptions ride #310 round 2 (ADR 0098). Bespoke
stays only where the 29-Jul surveys found nothing shipped: prereg guard, verified cross-family
judge, prosecutor, tell-stripping blind, decision-rule verdicts.
**Source:** 28-Jul-2026 session — 5-lane verified audit (10 confirmed findings, 0 refuted, gates
all green), grok-4.5 third-party opinion, three queued experiments executed. Evidence cites below.

## Verdict in one paragraph

Deterministic health is good (validate.py, adr-lint, all gate tests pass; manifests valid). The
defects are in truth-in-labeling and effort allocation: the front door makes claims the
instrument has retired or practice has broken, and 100% of open work + the last 10 days of
merges went to the measuring apparatus while the goal's first lever (adopter-felt skill
quality) produced nothing. grok-4.5's independent verdict: "self-referential spiral with one
real product win"; its top self-deception call: "mistaking the cleanup of the lab's conscience
for progress on the product the lab exists to improve."

## P0 — truth-in-labeling fixes (cheap, no measurement needed, one PR)

1. README.md:47 says "KEEP, strong" — the confidence vocabulary was retired by the live rule
   (benchstats.py:186: under an interval rule a weak/strong KEEP cannot exist). Drop the word.
2. Measured block lists 1 of 3 dev-skills: add honest lines for building-skills (iter3 revision
   NO MERGE; shipped version INCONCLUSIVE under grok headline judge, KEEP under claude —
   benchmarks/2026-07-18-bs-iter3-remeasure) and optimizing-context (09-Jul weak MERGE only).
3. Measured block presents verdicts as settled while #310 (instrument unconverged) and #317
   (contaminated DV) are open — add the standing caveat line grok recommended.
4. pdca-workflow/README.md:55-56,98 cite ADR 0065 and 0066/0076 — deleted 28-Jul by #318;
   point at the retired-ids map targets (docs/decisions/README.md:31).
5. ADR 0089(b) missed one site: benchmarks/2026-07-12-pdca-retrospect-recall/build_substrates.py
   still carries the stale benchmarks/lib/README.md cite.
6. skill-bench/README.md opens with unmeasured superiority claims — carry measured status or cut.
7. dev-skills plugin ships 3 tombstone files pointing at skill-bench paths absent from a
   dev-skills-only install — relocate or cut.
8. building-skills/SKILL.md hardcodes validate.py's NAME_MAX/DESC_MAX/TOC_THRESHOLD — defer to
   the script (budgeted file: measure headroom first).
9. Lows (fix in passing): "7x-cheaper" is measured 6.6x; "3+ cases" floor stated in 4 files;
   ADR 0016 Enforced line omits retrospect/SKILL.md.

## P1 — the one big call (owner /decide): "never on faith" vs practice  [HIGH finding]

18 commits since 19-Jul edited measured skills' content with no re-measure (ADR 0024 2(d));
last benchmark dir added 18-Jul. Options: (a) re-measure the three skills as now shipped;
(b) amend ADR 0024/README to an honest scope ("measured at baseline + re-measure debt ledger");
(c) revert unmeasured edits. Evidence for the decision: at G=6 the MDE is ~0.35 (coverage sim),
so per-edit re-measures are underpowered — argues for (b) plus BATCHED re-measures at G>=8.

## P2 — instrument decisions, evidence now in hand (/decide each, then close the issue)

- **#303 CLOSE-ready:** Monte Carlo (3k sims/condition, 3 DGPs, G=4-8, paired-delta design
  matching clustered_delta): t-interval coverage 0.948-0.970 (at/above nominal); exact sign-flip
  permutation CANNOT reject at alpha=.05 below G=6 (min p .125/.0625); wild bootstrap wider at
  G=4-5, no better coverage. KEEP t. Residual is POWER, not interval family: strong claims need
  G>=8. Sim: scratchpad coverage303.py, results table in session log.
- **#317 decide instrument:** measured trigram containment own-skill 1.4-3.6% vs cross-skill
  0.1-0.5% — verbatim leakage small but systematically positive (building-skills highest).
  n-grams UNDERSTATE the real coupling: grok's read of the evals found house doctrine as the DV
  ("frontmatter order", "cut Background") in building-skills + engineering-principles.
  Recommend: adopt per-benchmark overlap report as standing caveat (cheap, done once), and
  require task-value outcomes (#317 option 3) for FUTURE benchmarks of doctrine-heavy skills.
- **#310 decide disposition:** residual-risk ADR now vs sweep rounds 2-6. grok: stop the loop,
  route the 38 by rung in one sitting. sweep-state says round 2 of 6 owed. Recommend: one
  consolidated round 2 (fix-verification of #318's repairs + the control-integrity class), then
  the residual-risk ADR regardless of quiet.
- **#302 KILL the $25 grid, keep the question:** zero-cost read (28-Jul) captured most value —
  building-skills covers ~37/49 of Anthropic's guide (47.9% of the competitor corpus), the 7
  real omissions are <1.5k chars, and the plausible effect collapses below the G=10 MDE
  (0.17-0.26). Replace with: (i) apply the 4 lean reference-file edits from the comparison
  (~800 chars, headroom exists; description-order divergence recorded as deliberate); (ii) free
  read of obra's remaining ~50k non-Anthropic doctrine; (iii) NEW cheap pre-reg for the real
  question the guide raised (C5): building-skills vs bare — Anthropic itself claims the skill
  shouldn't need to exist; live loss condition for ours.
- **#252 stays blocked** (correctly): ep corpus touched again 28-Jul (#319). Unblocks after P1.

## P2b — naming + field position (research 28-Jul, owner call)

github.com/skill-bench org (skill-bench.dev, skill-eval-action, updated 22-Jun-2026) owns the
literal name this plugin adopted 13-Jul (ADR 0055) — search collision is real. benchflow-ai's
SkillsBench (arXiv:2602.12670, 1.6k stars) owns the adjacent mindshare; it is a fixed-corpus
leaderboard, NOT a BYO-skill harness, so it is a complement, not a substitute (verdict:
"reinventing badly" NOT supported; paired-arms idea predates us, the judge-integrity +
cost-matched + pre-registration layer exists nowhere else). Decide: rename plugin vs README
disambiguation (shipped 28-Jul) suffices. skill-bench README overclaim ("of the field") fixed
in PR #321.

## P3 — rebalance toward lever 1 (grok stop-list, owner direction)

Stop: open-ended instrument audits; expanding pdca ceremony; pre-reg drafting without a spend
decision. Start: building-skills iteration 4 (char-negative reshape — iter3's own ledger names
it); optimizing-context re-measure; both AFTER P1 settles the re-measure bar.

## /sweep evaluation (28-Jul, bench discipline, no spend)

Structural PASS: validate.py OK; 239-char always-loaded description (no trigger collision with
retrospect/verify/red-team); 5,067-char body on invoke; verdict logic one-homed in
sweep-state.mjs with passing decision-logic tests; n=1 productive use (38 verified findings,
honest RUNNING verdict). Paired measurement QUEUED behind #317/#303 decisions — single-shot
eval format cannot capture a multi-round convergence discipline, and measuring it now through a
contested DV would produce an untrustworthy KEEP. Differentiation claims stay queued-for-
measurement per house rule.
