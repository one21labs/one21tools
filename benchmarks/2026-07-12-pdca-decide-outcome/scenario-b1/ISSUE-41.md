# Issue #41 — pdca-workflow: tiered-agent execution (Sonnet plans/orchestrates, Haiku implements) — empirically test


## Idea (owner, 2026-07-08) — for AFTER the current skills/agents benchmark batch
Redesign pdca-workflow so the **bulk of implementation work is done by cheaper/faster models**, for time + cost efficiency, under a cost-tiered agent hierarchy:
- **Main / planning / orchestration agent** — a top-tier model. **Opus may earn its place ONLY here** (as the single main agent); the tier assignment is **the user's choice, and configurable**. Sonnet 5 can also fill this role and drive workers.
- **Workers** — **Haiku** (and Sonnet) do the bulk of the implementation.
- **Pattern**: main agent plans -> spawns workers to implement -> validates their work -> iterates the workers until correct.
- Model-per-tier is user-configurable; the empirical test compares configurations (e.g. Opus-main vs Sonnet-main, Haiku vs Sonnet workers).

## Scope
The pdca-workflow plugin's build/implementation flow (tech-lead -> implementation in the /decide loop; the "Do" phase). The orchestrator validates worker output and re-dispatches until it passes.

## Must be empirically tested (ADR 0024)
Do NOT adopt on assertion. Measure each tier configuration vs a single-model baseline on:
- **Quality**: task pass rate (the benefit-benchmark; the hermetic harness in `benchmarks/2026-07-08-skills-hermetic/` is reusable).
- **Cost + time**: tokens and wall-clock per task.
Adopt the configuration that holds quality at materially lower cost/time. Record the result (append-only snapshot) either way.

## Timing / dependencies
After the current skills + agents benefit-benchmark batch completes. Related: ADR 0024 (cost-justification loop), ADR 0023 (hermetic executor).

---

## Comment 1 (2026-07-09T01:43Z) — Test plan (pre-registration) — lean, empirical

Registered before running to avoid fishing for a favorable cut. Reuses the hermetic harness + eval sets + blind-grade pipeline in `benchmarks/2026-07-08-skills-hermetic/`.

**Question.** Does a tiered config (top model plans + validates, cheap model implements, iterate) match solo-top-model quality at materially lower cost/time?

**Hypothesis (falsifiable, pre-set margins).** Tiered (Sonnet plans+validates / Haiku implements / iterate <=3) is quality-**non-inferior** to Sonnet-solo (pass-rate delta >= -0.05, eval-clustered 95% CI) at **>=30% lower total tokens** (or wall-clock). **Null:** no cost/time saving at equal quality, or quality drops materially.

**Independent variable - 4 arms, same tasks:**
1. Haiku-solo (cheap floor)
2. Sonnet-solo (baseline)
3. Opus-solo (quality ceiling)
4. Tiered: Sonnet main plans + validates -> Haiku worker implements -> Sonnet validates -> re-dispatch with feedback, <=3 cycles. (Also test Opus-main once Sonnet-main is characterized.)

**Dependent variables (per run):** pass rate (all-expectations-met, blind-graded); **total tokens summed across ALL agents** in the config (the tiering tax counts); wall-clock. Headline efficiency = quality per 1k tokens.

**Method (lean):**
- Tasks: **8** implementation tasks from the existing eval sets, chosen for a **Haiku->Opus quality gradient** (tiering can only add value where the solos diverge; a task all arms pass carries no signal). Pre-screen with a 1-rep Haiku-solo vs Opus-solo pass; drop saturated tasks.
- **3 replicates** per (task x arm). Capture tokens via `claude -p --output-format json` (usage), wall-clock via `time`.
- **Blind** grade against each eval's expectations, **independent grader distinct from all 4 executor tiers** (ADR 0019). The tiered arm's internal validator sees ONLY the task, never the grading expectations - no teaching to the test.

**Analysis (ADR 0019/0024):**
- Per task: pass rate per arm; headline = eval-clustered mean delta (Tiered - Sonnet-solo), 95% CI.
- Cost/time: median total per arm; place all 4 arms on a quality-vs-cost frontier.
- **Sequential escalation:** add reps/tasks only where a CI straddles the decision boundary; stop when unambiguous.

**Decision rule (pre-registered).** Adopt Tiered if delta vs Sonnet-solo >= -0.05 AND tokens <= 0.7x Sonnet-solo (or wall-clock <= 0.7x). Also report whether Tiered reaches **Opus-solo quality at sub-Opus cost** (the real prize). Record the result either way (append-only snapshot; ADR 0024).

**Threats / controls:**
- **Task gradient** - without a Haiku<Opus gap the test is uninformative; the pre-screen enforces it.
- **Honest cost** - sum tokens across main + workers + every validation/retry; the orchestration overhead IS the tax under test.
- **Validator fidelity** - measure the main-agent validator's false-accept / false-reject vs the final grader; a validator that rubber-stamps bad work invalidates the loop (report it).
- **Grader independence** - blind grader is a distinct model from all executor tiers.

**New code needed (small):** a tiered-orchestration script (plan -> dispatch -> validate -> re-dispatch). Everything else is reused. Runs AFTER the current skills/agents batch.

## Comment 2 (2026-07-09T18:09Z)

Concrete poka-yoke gap surfaced by this session's retrospect: 5 merged `*.workflow.js` still omit `model:` on their grader/worker `agent()` calls, so a rerun silently executes on the session model (Opus). Tracked as #53. The empirical tiering test this issue asks for should land alongside that fix; #54 asks whether a static grep-check should permanently gate it.

## Comment 3 (2026-07-09T21:18Z) — Execution design (drafted 2026-07-09; the issue's pre-registration validated against actual code)

- 4 arms: Haiku-solo / Sonnet-solo / Opus-solo / Tiered (Sonnet plans+validates -> Haiku implements, <=3 cycles). Recommend deferring Opus-main per the pre-reg's own sequencing.
- Tasks: 8 implementation-shaped evals from skills/*/evals/evals.json (pre-screen 1-rep Haiku-vs-Opus, drop saturated); 3 reps per (task x arm).
- Metric: blind pass rate (reuse grade.workflow.js + prosecutor verbatim) + total tokens across ALL agents per config + wall-clock.
- New code: one tiered-orchestration Workflow script with model: set per role (the #53 lesson); everything else reuses blind.py/aggregate.py patterns.
- Cost: ~250-300 agent invocations.

**Owner calls before spend:** (1) grader independence is unsolvable with 3 tiers (arms exhaust Haiku/Sonnet/Opus) — accept the Sonnet-grades-Sonnet residual (as ADR 0019 already does) or defer; (2) which hermetic controls carry over to a tool-using implementation task (user-CLAUDE.md relocation yes; tool-deny impossible); (3) retry-cap + validator->worker feedback format in the new script.
