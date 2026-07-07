# Handoff — description ablation + remaining eval-validity work

Written for a fresh Claude instance picking up after the 2026-07-07 toolkit grid. Everything
you need is in this repo; nothing depends on the originating session's scratchpad. Read the
protocol first: `skills/building-skills/references/empirical-evals.md` (ADR 0013 + 0019).

## Primary next task: description ablation (always-loaded token optimization)

**Why it matters most.** A skill has two cost surfaces. The SKILL.md **body + references** load
*on demand* (only when the skill fires) — that is what the paired benchmark values and what
Tier-2 section ablation optimizes. The **description** (frontmatter) is the ONLY *always-loaded*
part — it sits in every request's context so the model knows the skill exists. So description
bytes are the most expensive bytes in the system, and trimming them (without losing trigger
accuracy) is the highest-ROI optimization here. And it is CHEAP: it rides the trigger runner
(one `claude -p` per query, no executor+grader), so unlike body ablation you can ablate
aggressively.

**Method.**
1. Baseline trigger-test each skill's current description: TP rate (fires on should-fire queries)
   and FP rate (fires on adjacent should-not-fire queries).
2. Ablate — drop a clause, shorten, remove an example trigger word — and re-run the (cheap)
   trigger set via the runner's `--description` override (no SKILL.md edit needed to test).
3. Keep the SHORTEST description that holds TP and does not raise FP. That trimmed string
   becomes the skill's new always-loaded footprint.

**The kit (all in `trigger-kit/` here):**
- `<skill>-queries.json` — 8 should_fire + 8 adjacent should_not_fire per skill (fresh-authored).
  Convert to the runner's schema: a flat list of `{"query": ..., "should_trigger": true|false}`.
- `runner-patches.diff` — 3 fixes to skill-creator's `run_eval.py` REQUIRED in this environment
  (hard-fail on unrelated first tool call; inherited-stdin stall; single-message detection
  window). Delegate-don't-vendor (ADR 0013): `git clone https://github.com/anthropics/skills`,
  then apply this diff to `skills/skill-creator/scripts/run_eval.py`. File the 3 fixes upstream.
- `FINDINGS.md` — the environment caveat, critical to interpretation.

**CRITICAL caveat (read `trigger-kit/FINDINGS.md`).** Nested `claude -p` sessions in this
container inherit ~16 built-in skills; a query like "review this code for quality" fires the
real `code-review` skill over any planted description. So ABSOLUTE trigger rates measured here
are competitive, not isolated — do NOT report them as a skill's true trigger rate. Description
**ablation A/B is still valid** because both variants face the identical competitor field (same
logic as the CLAUDE.md contamination the paired benchmark tolerates). Frame results as
"variant B holds/loses vs variant A", never as "skill X triggers Y% of the time".

**Recording the result** (this is "what's after"):
- The trimmed descriptions are edits to `skills/<name>/SKILL.md` frontmatter → a feature branch
  off `main`; `validate.py` must stay `[OK]` (description-as-trigger rule still applies).
- Fold the description-ablation METHOD into `empirical-evals.md` (its one home) — the
  two-surface framing (always-loaded description via trigger runner; on-demand body via
  benchmark) belongs in the protocol.
- Record the decision as a **lite ADR** (`tier: lite`, the tier ADR 0020 just added) IF it is a
  settled method with no live trade-off; a full ADR only if a real trade-off surfaces.

## Then: the deferred grading-validity items (ADR 0019, activate at the next full benchmark)

Recorded in `empirical-evals.md` "Grading reliability under the Claude-only constraint":
1. **Planted-defect calibration** — first live run: inject known violations + known-clean into a
   small set, grade, report the grader's false-pass/false-fail rate per assertion class.
2. **Prosecutor pass** — re-examine each PASS with a fresh grader instructed to refute.
3. **Blinded re-grade** of a grid sample — tests ADR 0019's WEAKEST assumption (does blinding
   flip any cell's direction?). If yes → re-benchmark that skill blinded and supersede.
4. **Mechanize-first** — convert executable assertions in the eval sets to scripts/greps.
5. **Out-of-sample retest** of the engineering-principles loophole fix (#27) — the +0.133/+0.333
   flips are in-sample (same evals that diagnosed it); 2 fresh evals would confirm generality.

## Other loose ends (not code, handed to a human/other instance)
- PRs: `lite-adr-tier` and `benchmark-data` need PRs opened; #26 needs a retitle.
- Orphan remote branch `adr-0020-measurement-validity` should be deleted (superseded; the git
  proxy refuses delete-pushes from a session).
- File the 3 `run_eval.py` patches upstream at anthropics/skills.

## Retune re-benchmark result (this session's last running test)
See `retune-results.md` in this directory (appended when its grading completes) — the before
baseline for the 5 retuned evals is recorded there so the before/after is self-contained.
