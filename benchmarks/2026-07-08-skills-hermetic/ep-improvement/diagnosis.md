# engineering-principles — weak-cell diagnosis

Source: `benchmarks/2026-07-08-skills-hermetic/{results.jsonl,graded/verdicts.json,graded/arm_map.json,meta.json,outputs/}`
(worktree `C:\Users\ajmcc\projects\worktrees\one21tools-main`). Per-cell fraction-met, n=3 reps/arm,
computed directly from `graded/verdicts.json` + `graded/arm_map.json` and cross-checked against
`results.jsonl` (exact match):

| eval | with | without | delta | class |
|------|------|---------|-------|-------|
| 1 | 0.889 | 0.889 | 0.000 | tie (high) |
| 2 | 0.867 | 0.867 | 0.000 | tie (high) |
| 3 | 0.778 | 0.722 | +0.056 | win — preserve |
| 4 | 0.733 | 0.533 | +0.200 | win — preserve |
| 5 | 0.067 | 0.067 | 0.000 | tie (near-zero) |
| 6 | 0.267 | 0.400 | -0.133 | **loss — harmful** |

Correction to the orchestrator's framing: eval 1 is an exact tie (0.889 = 0.889), not with < without.
The four weak cells, in priority order, are **6** (only actively harmful cell), **5** (both arms
almost totally fail — the biggest untapped opportunity), and **1**/**2** (high-scoring ties where a
single recurring expectation blocks a clean win). Evals 3 and 4 are wins and are untouched by this
proposal except where noted below.

---

## Eval 6 — LOSS, harmful (0.267 < 0.400)

**Task**: hardcoded API URL duplicated in 3 files, demo in 1 hour, "no cleverness... just paste the
new URL into each of the three spots," plus a request to also bundle in retry logic and logging.

**Finding**: Expectation 1 ("single URL definition... not pasted as a separate literal into each
script") is **NOT MET in all 6 responses, both arms, all 3 reps each**. Every single response —
with the skill loaded or not — pasted three independent literals. This is the persistent failure;
it's why the cell scores 0.267/0.400 instead of near 1.0.

Quote, `references/ssot-enforcement.md` (old), Code table: `URLs hardcoded | API endpoint in
multiple places | Config/environment variable` — the content needed to pass Exp 1 already existed
in the reference. It was never surfaced or applied.

**Gap 1 — not surfaced for this task shape.** `SKILL.md`'s Quick Decision Guide trigger for SSoT
was `Duplicate definitions suspected` — phrased as *auditing existing/found* duplication. This
eval's shape is the opposite: the user is *instructing* the model to *create* three fresh literal
copies ("just paste... into each of the three spots"). That phrase doesn't pattern-match "duplicate
definitions suspected," so the reference is never consulted. This is a **not-surfaced** failure, not
a content-quality failure — the fix existed and was ignored because the trigger didn't fire.

**Gap 2 — no tie-breaker for the "fastest path" vs "SSoT" tension.** Even where the model
recognized *something* was being asked (all 3 with-arm reps flagged that bundling retry+logging was
risky), none treated the URL literal-vs-constant question as live at all — it silently complied with
"paste it in the three spots." Under "no cleverness, fastest path," creating a shared constant reads
as *extra* work/cleverness rather than the equally-fast, more-correct default. `references/
waste-identification.md`'s Overprocessing row ("unnecessary abstraction... YAGNI, simplicity") gives
the model a vocabulary for resisting structure but nothing that distinguishes "premature abstraction"
(bad) from "collapsing a duplicated literal to one constant" (an SSoT fix, not overprocessing) — so
under time pressure the ambiguity resolves toward "don't add structure."

**Compounding, rep-1-specific**: with-arm rep 1 (`outputs/engineering-principles.6.with.1.txt`)
scored 0/5 — worse than every other rep of either arm — because it went ahead and bundled the
retry+logging despite flagging the risk ("I kept both minimal... but if you want zero risk, just do
the URL swap"). The without-arm's rep 1 (`...6.without.1.txt`) instead hard-recommended the minimal
path ("Given the clock, I'd paste only section 1 and ship"). Both arms' reps 2/3 behaved the same
(defer retry/logging correctly, still fail Exp 1) — so this one rep looks like ordinary model
variance on an already-present instinct (defer unrequested scope), not a second guidance gap. No new
content added for this; it would duplicate what's already working 2 of 3 reps.

**Fix applied**:
1. `SKILL.md` Quick Decision Guide SSoT row broadened: "Duplicate definitions suspected, **or asked
   to hardcode one value into several files**" — now pattern-matches an instruction to create
   duplication, not just found duplication.
2. `SKILL.md` "When to Read References" bullet added under ssot-enforcement.md: "Asked to
   paste/hardcode the same literal into multiple files, even under a 'fastest path' deadline."
3. `references/ssot-enforcement.md` Core Principle gains one paragraph resolving the tension
   directly: "**Time pressure is not an exemption.** ... one constant plus N imports is not slower
   than N literals, so declining it is not 'cleverness.' Defer only genuinely separate scope bundled
   into the same request (retry logic, logging, refactors); never defer the single-definition step
   itself." This also reinforces the already-working retry/logging deferral by naming it explicitly
   as the thing that SHOULD be deferred, sharpening the with/without contrast on Exp 2/3 too.

---

## Eval 5 — TIE at 0.067 (near-total failure, both arms — biggest opportunity)

**Task**: PM "already reviewed and approved" a one-line plan ("export a user's data, whatever format
is easiest, should be fast, ship next week"), explicit instruction "do not relitigate," asked only
to write the implementation task breakdown.

**Finding**: Expectation 3 ("does not silently choose a format, data scope, or performance target...
unknowns are surfaced as questions or decision tasks") fails in **6 of 6 responses**. Every response
— with or without the skill — picks JSON, picks a scope, and proceeds straight to a build-task list.
Quotes: with.1 `"Serialize to JSON and return as response"`; with.2 `"export format = JSON, access =
self-service only"`; with.3 `"Serialize to JSON (simplest format per plan)"`. This drags Exp 1, 2,
and 4 down with it (no gap list precedes the tasks; no stated "these answers are required before
implementation is safe").

**Gap 1 — the checklist never gets triggered.** `references/design-review.md` (old) "When to Use"
table only lists work-type triggers (new feature, significant change, substantial doc, bug fix,
spike). It has no row for "someone tells you the design phase is already done." The user's framing —
"already approved," "do not relitigate," "just... implementation tasks" — actively signals "this is
implementation, not design" and there is nothing in the reference contradicting that signal. The
`Software Design Checklist` (Problem Definition: measurable success criteria, explicit scope
boundaries; Interface Design: input/output contracts) is exactly the content that would catch this
plan's gaps — but it's never read, because nothing tells the model "approval status doesn't answer
whether this checklist was actually run."

**Gap 2 — the Go/No-Go section is agnostic on authority vs completeness.** Old "Ready to implement
if" list included "Stakeholders have reviewed and approved" as one bullet among several (checklist
items addressed, fallback plans, no blocking unknowns) — an AND, not a substitute — but nothing
states that explicitly, so a model under "don't relitigate" pressure has no textual anchor to resist
treating approval as sufficient on its own.

This is the single highest-value fix in this pass: the with-arm currently gets **zero benefit** from
loading a skill whose most relevant reference document (design-review.md, ~6.5KB of exactly the
right checklist content) never gets read for this task shape.

**Fix applied**:
1. `references/design-review.md` "When to Use" table gains a row: `Told a plan is "already
   approved," asked only for a task breakdown | **Yes** - approval is a process signal, not proof
   the checklist below was actually satisfied; check it anyway`.
2. `references/design-review.md` Go/No-Go Decision section gains a lead-in paragraph: "**Approval is
   not completeness.** 'The PM approved it' or 'don't relitigate' answers *who signed off*, not
   whether the items below are actually filled in. A one-line approved plan that never states the
   data scope, contract, success criteria, or error handling still has those gaps open — surface
   them as blocking questions or decision tasks, sequenced before the build tasks, even when told
   not to relitigate."
3. `SKILL.md` Quick Decision Guide row broadened: "Starting new work, **or told a plan is 'already
   approved'**" and a matching bullet added under "When to Read References" for design-review.md.

---

## Eval 1 — TIE at 0.889 (high-scoring, one recurring gap)

**Task**: post-incident RCA for a silently-empty export file, three occurrences, different triggers.

**Finding**: Expectation 6 ("a verification step... e.g. inject an empty export and confirm the
alert fires") is NOT MET in 4 of 6 responses (2 of 3 with-arm reps, 2 of 3 without-arm reps) — the
single most common miss across both arms. Responses consistently list corrective *actions* with
justification columns ("Why it addresses root cause") but never state how the team will *actively
prove* the fix works. Quote, `outputs/engineering-principles.1.with.1.txt`: the "Success Criteria for
Closing This Incident" section states desired end-states ("Monitoring alerts on output content/data-
quality signals, not exit code alone") but never a test that exercises them.

**Gap — the template's Verification slot is a content-free placeholder.** Old
`references/root-cause-analysis.md` Output Template: `### Verification \n [How we'll know the fix
worked]`. This is generic enough that "we'll monitor going forward" or a restatement of the
countermeasure's intended property satisfies it on a shallow reading — it doesn't model what a
passing answer looks like (an active fault-injection test), so the model has nothing concrete to
imitate.

**Fix applied**:
1. Output Template Verification placeholder rewritten to name the pattern explicitly: "A concrete
   test that proves the fix works — inject the failure condition and confirm the safeguard fires
   (e.g., run the job against a query that returns zero rows and confirm the alert triggers). Not
   'we'll monitor going forward' and not a restatement of the countermeasure's intended properties."
2. `Common Mistakes` table gains a matching row so the point lands even for a reader who skims past
   the template: `Verification = "we'll monitor going forward" | Doesn't prove the fix works | State
   how you'll actively trigger the failure condition and confirm the safeguard catches it`.

---

## Eval 2 — TIE at 0.867 (high-scoring, one recurring gap)

**Task**: restructure duplicated/contradictory docs (setup steps, a timeout value, a file-specific
CLAUDE.md rule, a "Lessons learned" backstory section) to one canonical home each.

**Finding**: Expectation 4 ("'Lessons learned' section is deleted outright... not merged, relocated,
or preserved in condensed form") fails in 3 of 6 responses via the **same specific loophole** every
time: offering CHANGELOG.md as an acceptable destination. Quotes: with.1 `"If the team wants a
durable changelog, it belongs in CHANGELOG.md, not CLAUDE.md"`; with.2 `"If the team wants the
history kept somewhere, put it in CHANGELOG.md, or rely on git log"`; without.3 lists canonical
location as `"Git history / commit messages... — or a CHANGELOG.md if the project keeps one."` All
three graders flagged this as "precisely the forbidden relocation."

**Gap — an enumerated blocklist with an unlisted exit.** Old
`references/ssot-enforcement.md` Documentation-violations row: `git history is the SSoT for backstory
— state current truth, delete the story outright; never relocate or condense it into ADRs or
comments`. The rule bans two *specific* destinations (ADRs, comments) rather than stating the
principle unconditionally. A model reading this literally can offer CHANGELOG.md — not on the list —
as compliant, which is exactly what happened in 3 of 6 responses, independent of which arm.

**Fix applied**: broadened the same row's fix column to close the enumerated-list loophole: "...never
relocate or condense it into any other document (ADRs, comments, a CHANGELOG, a wiki page, a new
'history' file)." No structural change — same row, same file, same location — just removes the
implicit "anything not named is fine" reading.

---

## Preserved: evals 3 and 4 (wins, untouched)

Both wins share a *related but separate* pattern worth flagging for a future pass, not acted on here
to avoid scope creep on an already-winning cell: models on both arms consistently **hedge** a
correct-but-aggressive elimination into a softer, reversible version. Eval 3 Exp 2 ("sign-offs
flagged as redundant to eliminate/collapse, not merely parallelized") fails in all 3 with-arm reps —
responses parallelize/risk-tier the three sign-offs instead of collapsing them. Eval 4 Exp 2 ("delete
the scaffolding, not leave it dormant") fails in all 3 with-arm reps and all 3 without-arm reps —
responses "shelve," "park behind a flag," or "keep the code, just don't finish it" instead of
deleting. Because eval 4's overall margin is the widest win in the set (+0.200) and eval 3 is also a
clean win (+0.056), and because `waste-identification.md`'s Overproduction row already says "delete
half-built speculation" in as many words, this reads as a general LLM softening instinct rather than
a skill-content gap — strengthening the wording further risks diminishing returns and was left out of
this pass. Flagging for whoever runs the next improvement iteration if these evals are still
targeted after a future difficulty pass.
