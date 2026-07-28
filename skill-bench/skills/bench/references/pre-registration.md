# Pre-registration — pre-run discipline for paid experiments

Read this when designing or pre-registering a paid experiment (a benchmark grid, an ablation,
any run that spends real executor budget). It extends ADR 0024 (cost-justification) and ADR
0025 (verdict methodology) UPSTREAM of the run; [empirical-evals.md](empirical-evals.md) owns
the measurement protocol itself.

## Pre-registration cites the settled methodology

A pre-registration CITES the verdict methodology — fraction-met headline with binary
all-expectations-met as secondary (ADR 0025), the eval-clustered CI unit (ADR 0019), the
sequential-escalation rule, cost accounting (ADR 0024) — instead of restating any of it, and
never names a metric the ADRs have superseded. A pre-reg whose stated metric predictably
floors (binary pass-rate floored three benchmarks running) invites exactly the fishing
accusation pre-registration exists to prevent.

## Cost-pilot before any grid

Run 2-3 cells of the MOST EXPENSIVE arm first; if any pre-registered gate is already decidable
from the pilot, stop and record the verdict. Unconditional — it reorders spend, it adds none.
(Live instance: a 216-cell tiered grid whose cost gate was decidable after ~5 cells, ~$0.60 —
roughly 90% of executor spend was saveable.)

## Saturation/floor pre-screen before any grid

Before the grid spends: run 1 rep of the CONTROL arm per eval/substrate; drop or harden any
where the control scores at or above a pre-registered ceiling threshold, and flag any that
floors at 0. An eval outside its discriminating band carries no signal in either direction —
a control that aces the eval proves the substrate restates the answer, not that the skill adds
nothing (the #172-I1 ceiling), and the mirror failure floored three benchmarks (ADR 0025).
Record the pre-screen result and any dropped/hardened eval in the dated dir BEFORE the grid.
Guardrail (ADR 0024): the pre-screen restores discriminating power — it is never
difficulty-tuning toward a desired verdict; a hardened eval may CONFIRM the negative
direction, recorded either way.

## No primed conclusions (ADR 0059)

Every pre-registration, experiment issue, and eval title states a FALSIFIABLE hypothesis
neutrally — kill conditions and bars up front, motivation labeled as grounding (never evidence),
a null recorded as an equally valid outcome. Titles pose the question, never the answer.
Advocacy wording is itself a contamination channel: agents read it.

## Infrastructure is never quality (#191)

Every generative step in an arm carries an output contract with one retry, or a pre-registered
ERROR-cell rule — above all the step producing the graded artifact. A cell whose graded artifact
fails the mechanical shape check (`lib/artifact_check.py`) is an ERROR cell, never a quality 0.
Before blinding, run the capture-symmetry sweep (`blind.capture_symmetry`) — arm-skewed emptiness
is an infrastructure defect to fix before grading, not signal.

## Design for signal (ADR 0065)

- **Gate or optimization?** — mandatory field (ADR 0062 two-stage doctrine): is this run a
  cheap go/no-go gate or a powered optimization? Powered designs are reserved for
  gate-passers.
- **Variance is a primary metric** — a skill's point is raising the mean while damping output
  variance; pre-register per-arm consistency (within-scenario rep variance / worst-rep score)
  alongside the mean deltas.
- **Power the design — two numbers, both stated before the run.** (1) The PRACTICAL BAR: the
  smallest difference worth paying context for, tested against the interval's LOWER bound so KEEP
  means "at least this much". Set after the fact it is worthless. (2) The SCENARIO COUNT that
  makes that bar reachable: `clusters_for(sd_between(prior_delta), target)`, at 80% power, sized
  from a prior run's measured spread rather than guessed (ADR 0076 applied to power). A grid
  sized below it can only return INCONCLUSIVE — spend with a known-null outcome.

## Sizing, at this repo's measured spread of 0.24

| To reliably call | scenarios (80% power) | at 50% power, for contrast |
|---|---|---|
| 0.40 | 5 | 4 |
| 0.25 | 10 | 7 |
| 0.15 | 22 | 13 |
| 0.10 | 46 | 25 |
| 0.05 | 181 | 89 |

The 50% column is what you get by sizing so the target equals the CI half-width — a design that
succeeds on a coin flip. It is shown only so the difference is visible; never plan from it.

**Variance is the cheap lever; scenarios are the expensive one.** At spread 0.24, six scenarios
reliably call only 0.34 or larger, so a real 0.18 effect needs 16. One run here achieved a spread
of 0.065, where six scenarios reach 0.09 and that same effect needs **four**. More reps per cell,
a tighter rubric, and harder scenarios that are not ceilinged all buy more than adding scenarios,
and cost less.

Two hazards in the sizing input itself. `sd` from a G=6 run carries df=5 — very noisy, and biased
low whenever the realized spread happened to be small, so the returned count is a FLOOR. And a
prior from a different comparison class is not a draw from the same spread at all: skill-vs-bare
priors do not size a skill-version comparison. Prefer a conservative pre-registered value or an
upper bound on `sd`.

Skill-versus-bare effects here have run 0.18 to 0.44, so that question is answerable at these
sizes. Skill-VERSION differences are far smaller, which is why a six-scenario grid comparing two
wordings can only return INCONCLUSIVE.

## Prior-art pass before designing a paid experiment

Before designing, ask: is the answer already known, and in what parameter regime does it turn?
If known, test the OPEN regime, not the settled one. Size-gated — required only above a
non-trivial spend threshold, never on small pilots (mandating research before trivial runs is
gold-plate).
