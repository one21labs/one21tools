# skill-assay program — executable plan (v2, post-vetting)

**Goal:** execute every outstanding skill-assay work item — rename, audit closure, instrument
decision, substrate adoption, first debt-paying re-measure — as owner-approved PRs.
**Architecture:** six phases, each its own PR behind an owner merge; phases that add ADRs are
SERIALIZED through the shared corpus budget (never parallel).
**Executor:** a fresh Claude Code session with only this plan and the repo. Resume by scanning
the checkboxes; a checked box means its verify command was run and passed.
**Governing skills in this repo:** `pdca-workflow:sweep` (Phase 2), `pdca-workflow:decide`
(Phases 3-4), `skill-bench:bench` references (Phase 5). Read each before its phase.
**Owner actions:** merge PRs; run `/plugin marketplace update one21tools` THEN
`/reload-plugins` after any plugin-touching merge; spend checkpoint at Phase 5.
**Out of scope, deliberately:** issue #302 (competitor-corpus experiment — not harness work);
lever-1 skill improvement (tracked in the repo-state plan); #310 items unrelated to this
program's phases.

## Vetting provenance (29-Jul-2026)

Draft vetted by five lanes; all grounded findings folded: grok-4.5 (cross-family, verbatim
plan + neutral question), opus (cold-start achievability — corpus arithmetic, gate coverage,
module roles), sonnet (adopter impact), haiku (mechanical surface re-derivation), and a lane
operating under obra/superpowers' `writing-plans` skill (checkbox resumability, File
Structure blocks, typed interfaces; its TDD granularity deliberately NOT applied to the
decision-gated phases 3-4).

## Global execution rules (every phase)

- [ ] G1. `git fetch origin main` before starting a phase; read the phase's governing ADR
  from disk. Never trust an agent's echo of a file write — read back from disk (a PM subagent
  fabricated writes twice in the planning session).
- [ ] G2. **Full local gate mirror** (gates.yml runs 13 steps; run ALL of these before every
  push, from repo root):
  ```
  python3 skills/building-skills/scripts/validate.py <every skill dir touched, incl. skill-bench/skills/bench>
  python3 skills/building-skills/scripts/validate_test.py
  node pdca-workflow/scripts/adr-lint.mjs docs/decisions
  node --test pdca-workflow/scripts/*.test.mjs scripts/*.test.mjs skill-bench/scripts/*.test.mjs
  python3 skill-bench/scripts/lib/check_reachability.py skill-bench/scripts skill-bench/scripts/lib skills/building-skills/scripts
  set -e; for t in skill-bench/scripts/*_test.py skill-bench/scripts/lib/*_test.py; do python3 "$t"; done
  node scripts/check-relocated-paths.mjs
  node scripts/check-cite-ownership.mjs
  node scripts/check-restatement.mjs
  node scripts/check-workflow.mjs benchmarks && node scripts/check-workflow.mjs skill-bench
  node scripts/check-references.mjs   # fails on new external URLs without a fetch-audit record (ADR 0079)
  ```
  (`set -e` in the python loop is mandatory — a bare loop returns only the last test's status.)
  check-pr-body.mjs and the hook tests run in CI; mirror locally only if touched.
- [ ] G3. **ADR corpus budget is FATAL at 200,000 chars and is nearly full: 194,409 on the
  #321 branch = 5,591 headroom.** Per-record caps: lite 2,000; full 9,000 (8,000 is an
  advisory WARN, not the cap). Growth is PAID by compacting, never granted (char-budget.mjs).
  Before ANY phase that adds a record: run adr-lint (it prints the corpus total), compute
  `projected_record + 500 reserve <= headroom`; if not, compact FIRST — list the 5 largest
  records by `wc -c docs/decisions/*.md | sort -n | tail -5` and cut muda there as its own
  commit. This plan's records are all LITE (<=2,000) for this reason.
- [ ] G4. Budgeted-file edits (SKILL.md, ADRs near cap, references): measure headroom first
  (`wc -c` vs cap); if an addition doesn't fit, land the funding cut as its own Edit BEFORE
  the addition. Skip the hunt when headroom already covers it.
- [ ] G5. PR discipline: body = Purpose/Changes/Testing/Deferred + the line
  `*Disclosure: written by Claude (Claude Code) under the direction of the repo owner.*`;
  stage explicit paths only; commit message written from `git diff --cached --stat`; read the
  muda-review CI comment before merge and answer every finding.
- [ ] G6. Counts in this plan are a map, not an authority — **re-derive every surface with the
  stated grep at execution**; the live grep wins.

## Phase 0 — clarify ADR 0097 in place (on the OPEN #321 branch, before merge)

**Why:** 0097 as accepted reads as a directory move ("every ADR file token into skill-bench/
repoints"; "a rename IS a relocation"; grep-clean acceptance). A directory move strands ~35
`skill-bench/` cites in frozen benchmark dirs (the MOVED-marker exemption covers only `.md`
under manifest `skills[]` dirs — the skill-bench plugin has no `skills[]`), fails adr-lint on
0098's Enforced line, and rebuilds the shim forest 0089's Act removed. Verified by three
lanes independently.
**Authorization:** 0097 rides the still-open PR #321 — revising an unmerged record in place is
the template's own rule ("revise it in place — never a second ADR"); the owner's #321 merge
review approves the revision.

- [ ] 0.1 Edit `docs/decisions/0097-rename-skill-assay.md` — replace decisions 4-6 with this
  text (verbatim; note it avoids the underscore env literal so Phase 1's acceptance grep
  stays clean — the prefix is described, not spelled):
  ```
  4. The DIRECTORY stays `skill-bench/`. Frozen benchmark dirs cite executable paths under it
     that the MOVED-marker exemption deliberately does not cover; a path move rebuilds the
     shim forest the 0089 Act removed. Only NAME-POSITION surfaces change.
  5. Name-position surfaces, all mandatory: (a) marketplace plugin name + a `renames` map
     entry old->new; (b) plugin.json name (descriptions stay byte-identical); (c) the env-var
     prefix (SKILL BENCH -> SKILL ASSAY, underscore-joined) everywhere outside benchmarks/;
     (d) install strings `skill-bench@one21tools`; (e) GLOBAL_TELLS gains the new name and
     KEEPS the old (historical leak pattern for dated records). The `/bench` skill name and
     every `skill-bench/` PATH token are unchanged.
  6. Acceptance: the Phase-1 checklist of its executing plan — per-surface greps returning
     zero name-position hits — replaces a bare repo-wide grep, which the retained directory
     makes unsatisfiable. `benchmarks/**` and this record's own prose are exempt.
  ```
  Keep decisions 1-3 and 7, Justification, assumptions (drop the "char-identical" claim only
  if wording changes lengths), Rejected (the "name-only rename" rejection now reads as
  rejecting the TELLS-less half-rename — reword its line to say exactly that), triggers.
- [ ] 0.2 Reconcile frontmatter `summary` + title with the directory-stays decision.
- [ ] 0.3 Verify: `node pdca-workflow/scripts/adr-lint.mjs docs/decisions` exit 0; corpus
  total noted; `wc -c docs/decisions/0097-*.md` <= 9,000.
- [ ] 0.4 Update PR #321's body (gh api PATCH — `gh pr edit` fails here) to enumerate ALL
  records it ships: 0095, 0096, 0097 (revised), 0098, 0089 Act, 0093 amendment, 0013/0024/
  0055 corrections.
- [ ] 0.5 Push to `p1-decide-0095`. Gates green in CI. **Owner merges #321.**
  *Abandonment caveat: Phase 0 lives on #321's branch — abandoning it means reverting a
  commit there, not deleting this plan's branch.*

## Phase 1 — the rename PR

**Entry:** #321 merged. Branch `rename-skill-assay` off fresh main.
**File structure (edit targets):** `.claude-plugin/marketplace.json` (name, renames map);
`skill-bench/.claude-plugin/plugin.json` (name); `skill-bench/scripts/lib/contamination.py`
(GLOBAL_TELLS); env-prefix files — re-derive with `grep -rln "SKILL_BENCH_" . | grep -v
benchmarks` (map as of 29-Jul, ~48 occurrences/11 files: config.py, judge.py, config_test.py,
judge_test.py, substrate.py, substrate_test.py, hermetic_driver.py, references/judging.md,
references/substrate.md, skill-bench/README.md, docs/decisions/0058 historical cite — leave
0058 as history, it names what the var WAS); install strings — root README.md,
skill-bench/README.md.

- [ ] 1.1 **Resolve the `renames`-map shape first** (it exists nowhere in this repo to copy):
  WebFetch `https://code.claude.com/docs/en/plugin-marketplaces` (or current docs) and
  confirm key placement (top-level vs per-plugin) + minimum CC version; record both in the PR
  body. If the docs don't settle it, test in a scratch marketplace clone before editing the
  Sacred manifest. Do not guess.
- [ ] 1.2 marketplace.json: plugin `"name"` -> `"skill-assay"`; add the renames map per 1.1;
  `"source": "./skill-bench"` UNCHANGED. plugin.json `"name"` -> `"skill-assay"`.
  Verify: `jq` both files parse; descriptions byte-identical.
- [ ] 1.3 contamination.py GLOBAL_TELLS: add `r"skill-assay"`, keep `r"skill-bench"` with a
  one-line comment (historical leak pattern). Verify: the contamination tests in the G2 loop.
- [ ] 1.4 Env prefix swap, one file per checkbox, `set -e` python test loop after EACH:
  re-derive the list (G6), then for each file: replace `SKILL_BENCH_` -> `SKILL_ASSAY_`,
  run its `*_test.py` neighbor. Char-identical (12 chars both), so no budget motion.
- [ ] 1.5 Install strings: `grep -rn "skill-bench@one21tools" .` -> currently root
  README.md:20 + skill-bench/README.md:4; replace with `skill-assay@one21tools`. The
  `/bench` COMMAND STAYS `/bench` (skill name unchanged — do not rename it). There are no
  live `skill-bench:bench` namespace strings outside records (verified 29-Jul; re-grep; if
  zero, skip — do not edit ADR prose to manufacture hits).
- [ ] 1.5b **Adopter migration (sonnet lane — the silent-break fix).** (i) Env-var alias
  window: in `config.py` and `judge.py`, when a new-prefix var is unset, read the old-prefix
  name and print ONE loud stderr deprecation line naming both (mark those lines
  `# deprecated alias (one release)` — the 1.7 acceptance grep exempts lines carrying that
  marker). Alias ships for one release, then a follow-up removes it. (ii) README
  Requirements section gains: automatic plugin-name migration needs Claude Code >= 2.1.193
  (docs-confirmed); older CLIs report plugin-not-found for the old name — remove + re-add
  the marketplace once. Both documented in the PR body.
- [ ] 1.6 DO NOT touch: `benchmarks/**`; any `skill-bench/` PATH token (directory stays);
  docs/decisions prose (records are history; 0097 describes the mechanics); docs/pdca logs.
- [ ] 1.7 Acceptance (all must hold): `jq -r '.plugins[]|select(.source=="./skill-bench").name'
  .claude-plugin/marketplace.json` -> `skill-assay`; renames map present per 1.1;
  `grep -rn "skill-bench@one21tools" .` -> 0; `grep -rn "SKILL_BENCH_" . | grep -v
  benchmarks/ | grep -v docs/decisions/ | grep -v "deprecated alias"` -> 0 (the alias shim's
  old-name reads are the sole sanctioned survivors); full G2 mirror green.
- [ ] 1.8 PR (cite ADR 0097). **Owner merge = consent to execute (0097 decision 7).** After
  merge: owner runs marketplace update + reload, then confirms their install migrated (0097's
  WEAKEST signal). If migration fails -> revert PR; fall back to `displayName` per 0097.

## Phase 2 — #310 rounds 2-3 + residual-risk record

**Entry:** #321 merged. Governing: ADR 0098 + `pdca-workflow:sweep` skill (read both).
**Scope note:** the sweep's own stop rule needs TWO consecutive quiet rounds — one round
cannot reach CLEAN. Budget: rounds 2 and 3; hard stop after round 3 regardless of verdict
(the disposition record then routes what remains). Ceiling: cross-family lane via
`node pdca-workflow/scripts/crosscheck.mjs` (in-repo path; if it returns FRAME-UNCHECKED,
record that in the round line — it is a valid xfam answer, not a blocker).

- [ ] 2.1 Round 2 per the sweep skill: same surface as round 1 (`skill-bench/scripts`,
  `skill-bench/skills/bench/references`, `benchmarks/lib`), independent lanes, verified
  findings only, append the round line to `docs/pdca/sweep-skill-bench-<date>.jsonl`.
  Stats-menu items (AC1/phi, McNemar+Newcombe, permuted expectation order, negative-control
  fixture, look-cap prereg field, UCB pilot SD) are implemented ONLY when a lane reproduces
  the defect live this round — the round's verify lane is the arbiter; each fix ships with a
  test (CLAUDE.md gating-script rule).
- [ ] 2.2 Round 3 same shape. Ask `node pdca-workflow/scripts/sweep-state.mjs <log> --max 6`
  for the verdict; relay it verbatim.
- [ ] 2.3 Residual-risk record, tier LITE (<=2,000 — G3 headroom cannot fund a full record):
  route all 38 round-1 ids + any new ones by rung (gate / fixed / accepted-with-reason,
  compressed table). #310: close ONLY if sweep-state's verdict permits reading the surface
  as converged; otherwise NARROW the issue to the named survivors and say the verdict
  verbatim. Explicitly disposition the #318 KEEP-rule repair (verified fixed?) and state
  whether #303 blocks trust in new measurements (its evidence: t coverage holds; power is
  the constraint).
- [ ] 2.4 One PR: fixes + tests + round log + the lite record. G2 mirror green.

## Phase 3 — split: 3a leakage audit (unblocked) + 3b instrument /decide (gated)

**3a entry: #321 merged — NOT gated on Phase 2** (sonnet lane: the audit is already decided
by 0098's ADD; holding the one no-downside adopter protection hostage to a possibly-
non-convergent sweep repeats the delay class the plan exists to end). 3b entry: Phase 2's
record exists. Governing: `pdca-workflow:decide`; ADR 0098; #317's 28-Jul comment.

- [ ] 3a Implement the leakage audit (contract at 3.2 below) as its own small PR the moment
  its spec paragraph is written; the later /decide may refine thresholds, not existence.
- [ ] 3.1 (=3b) `/decide` on expectation authorship. Options from #317: blind authoring;
  per-benchmark overlap caveat (instrument already exists — the n-gram containment method in
  #317's comment, reuse it, do not invent a second); task-value outcomes for doctrine-heavy
  skills. Record: LITE (<=2,000) unless assumptions force full — then fund via G3 first.
  Gates per the decide skill (this ships: one fresh adversary minimum).
- [ ] 3.2 Implement the leakage audit with a TYPED contract Phase 5 invokes (default; the
  /decide may amend): `python3 skill-bench/scripts/leakage_audit.py --skill <dir> --evals
  <evals.json>` -> exit 0 clean / 1 findings (stdout lists them); plus a paragraph in
  `skill-bench/skills/bench/references/pre-registration.md` (REFERENCE cap 12,000 chars;
  currently ~5,900 — measure first, G4). Script ships with a test.
- [ ] 3.3 #317: close with the record cite, or narrow to named survivors. G2 green; PR.

## Phase 4 — Inspect AI substrate: /decide first; implement only if accepted

**Entry:** after Phase 1; NEVER in parallel with another ADR-adding phase (shared G3 budget).
**Evidence for the decide (verified):** seam `skill-bench/scripts/lib/substrate.py` —
`make_substrate(name, **kw)` dict dispatch; contract `run(self, prompts, arms, workdir=None)
-> [{prompt_id, arm, output}]`; promptfoo + native implemented; inspect-ai PLANNED in
README architecture. promptfoo is OpenAI-owned (Mar-2026) with a security pivot.
**Module roles, stated correctly:** `spend_guard.py` is a `--yes` refusal, nothing else;
the pilot ceiling lives in `cost_gate.py` (`gate(cells_total, pilot_cell_costs,
ceiling_usd)`, owner ADR 0052 decision 3 / ADR 0042). Inspect's runtime dollar/token limits
would be a NEW third layer (mid-run ceiling) — they replace neither module.
**The real design question the /decide must answer:** skill-bench arms are subprocess
commands (hermetic by arm-level tool denial); Inspect drives models through its own
provider/solver model. `InspectSubstrate` either (a) wraps a shell exec — forfeiting the
dollar limits that motivate the adoption — or (b) re-homes hermeticity into Inspect's
sandbox (bigger, buys the limits). The decide picks a/b/reject with a cost ceiling and an
abandonment trigger; "~10pd" is the b-branch floor, not an estimate of (a).

- [ ] 4.1 `/decide` with the above as the frame; record LITE if possible (G3). External
  URLs cited -> `scripts/check-references.mjs` demands a fetch-audit record in the same
  change (ADR 0079).
- [ ] 4.2 If accepted: own PR per the decided branch; adapter + config gen/parse + tests;
  native fallback retained; G2 green.

## Phase 5 — first G>=8 batched re-measure (pays ADR 0095's debt)

**Entry:** Phase 3 decided. Governing: ADR 0095 (read decisions 3-4 + triggers from disk);
`skill-bench/skills/bench/references/empirical-evals.md` "Authoring evals" +
`evaluating-your-own-work.md` + `pre-registration.md`.
**Cost, stated whole:** ~$16/skill (2 arms x 8 evals x 3 reps x ~$0.33) -> **~$63 for all
four measured skills**, the same figure 0095 used to reject an UNBATCHED re-measure — the
difference here is G>=8 power and the Phase-3 instrument discipline. Prescreen attrition
means authoring 3-4 evals/skill (prescreening 9-10) — price generation accordingly.
**OWNER SPEND CHECKPOINT: present the pre-registration + total + `ceiling_usd` (house rule:
2x estimate, so ~$130 for the full batch) and get explicit approval BEFORE generation.**

Per skill (one checkbox each: building-skills, code-standards, engineering-principles,
optimizing-context):
- [ ] 5.1 Author >=3 new evals per the authoring reference + Phase-3 discipline; run the
  leakage audit (3.2 contract) — exit 0 before any spend; record the eval-set diff vs the
  cited baseline AND the skill-expectation overlap number in the dated dir (0095 decision 4
  REQUIRES both while #317 is open).
- [ ] 5.2 Pre-register via the prereg_guard CLI (step 1 of evaluating-your-own-work.md):
  neutral hypothesis (ADR 0059), G, MDE from `keep_verdict()`'s `mde80`, cost + ceiling_usd.
- [ ] 5.3 Run `bench_skill.py` (cross-family judge default). If post-prescreen G < 8: the
  batch is DIAGNOSTIC ONLY (0095 decision 4 — it cannot discharge debt); trigger 0095's
  named decision point — invest in more evals or retire that skill's measured claim — and
  record which, before touching any claim.
- [ ] 5.4 If a skill is simultaneously in an ADR 0024 improvement loop: fold this batch into
  that loop's iteration 1 (0095's third trigger) — never pay twice.
- [ ] 5.5 Claims PR per 0095 decision 3: any added/upgraded measured claim cites the dir that
  measured the SHIPPED content; the PR body pastes the treatment-vs-live-body byte-compare
  output. Dirs append-only (ADR 0041). G2 green.

## Self-review (executor: confirm at start)

Every governing record maps to a phase: 0097 -> 0+1; 0098 -> 2 (+ scoping already shipped in
#321); #310 -> 2; #317 + 0098's ADD -> 3; substrate/adopt strategy -> 4; 0095 debt + #303
posture -> 5. 0096 is fully shipped by #321 (no phase). #302: out of scope (header).

## Sequencing + abandonment

Phase 0 now -> owner merges #321 -> **Phases 1 and 2 in PARALLEL** (no dependency; Phase 1
adds no ADR, so the G3 serialization is not violated) + **3a as soon as spec'd** ->
Phase 3b -> Phase 4 -> Phase 5. ADR-ADDING phases (2, 3b, 4) strictly serial through the
shared corpus budget (G3), regardless of file overlap. Phase 0's adopter gain is zero by
design (internal prerequisite — 0097 is not shipped to installs); Phase 2 is the highest
direct adopter value (it fixes the harness every adopter's own runs execute) — do not delay
it behind the rename. Abandoning the program = deleting this branch (exception: a landed
Phase 0 rides #321 and stays — reverting it means reverting that commit). Each other phase
is one PR with its own revert boundary; nothing mutates main without an owner-merged PR.
